import os
import socket
import sqlite3
import tempfile
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase

from colegio.grupos import NOMBRE_SECRETARIA
from colegio.services import configuracion
from colegio.services.instancia import adquirir_bloqueo
from colegio.services.respaldos import (
    Respaldo,
    RespaldoInvalido,
    archivo_sano,
    listar_respaldos,
    migrar_con_respaldo,
    respaldar,
    respaldar_completo,
    respaldos_a_conservar,
    respaldar_si_hubo_cambios,
    restaurar,
)

AHORA = datetime(2026, 6, 1, 12, 0, 0)


def crear_bd(ruta: Path, valores: list[str]) -> None:
    conexion = sqlite3.connect(ruta)
    conexion.execute("CREATE TABLE IF NOT EXISTS datos (valor TEXT)")
    conexion.executemany("INSERT INTO datos (valor) VALUES (?)", [(v,) for v in valores])
    conexion.commit()
    conexion.close()


def leer_bd(ruta: Path) -> list[str]:
    conexion = sqlite3.connect(ruta)
    try:
        return [fila[0] for fila in conexion.execute("SELECT valor FROM datos ORDER BY rowid")]
    finally:
        conexion.close()


class CarpetaTemporalTestCase(unittest.TestCase):
    def setUp(self):
        self._directorio = tempfile.TemporaryDirectory()
        self.raiz = Path(self._directorio.name)
        self.db = self.raiz / "colegio.db"
        self.carpeta = self.raiz / "respaldos"
        self._entorno = patch.dict(os.environ, {"COLEGIO_DATA_DIR": str(self.raiz / "datos")})
        self._entorno.start()

    def tearDown(self):
        self._entorno.stop()
        self._directorio.cleanup()


class RespaldoTests(CarpetaTemporalTestCase):
    def test_respaldo_es_valido_y_restaurable_con_los_mismos_datos(self):
        crear_bd(self.db, ["alumno-1", "alumno-2"])

        respaldo = respaldar(self.db, self.carpeta)
        self.db.unlink()
        restaurar(self.db, respaldo, self.carpeta)

        self.assertTrue(archivo_sano(respaldo))
        self.assertEqual(leer_bd(self.db), ["alumno-1", "alumno-2"])

    def test_respaldo_truncado_se_rechaza_y_el_original_queda_intacto(self):
        crear_bd(self.db, ["original"])
        corrupto = self.raiz / "corrupto.db"
        corrupto.write_bytes(self.db.read_bytes()[:50])

        with self.assertRaises(RespaldoInvalido):
            restaurar(self.db, corrupto, self.carpeta)

        self.assertEqual(leer_bd(self.db), ["original"])

    def test_restaurar_guarda_copia_previa_del_estado_actual(self):
        crear_bd(self.db, ["viejo"])
        respaldo = respaldar(self.db, self.carpeta, etiqueta="manual")
        crear_bd(self.db, ["nuevo"])

        restaurar(self.db, respaldo, self.carpeta)

        etiquetas = [r.etiqueta for r in listar_respaldos(self.carpeta)]
        self.assertIn("antes-de-restaurar", etiquetas)
        self.assertEqual(leer_bd(self.db), ["viejo"])

    def test_migracion_fallida_restaura_el_estado_previo(self):
        crear_bd(self.db, ["antes"])

        def migracion_que_falla():
            crear_bd(self.db, ["a-medias"])
            raise RuntimeError("fallo simulado")

        with self.assertRaises(RuntimeError):
            migrar_con_respaldo(self.db, self.carpeta, migracion_que_falla)

        self.assertEqual(leer_bd(self.db), ["antes"])

    def test_respaldo_periodico_omite_si_no_hubo_cambios(self):
        crear_bd(self.db, ["dato"])
        respaldo = respaldar_completo(self.db, self.carpeta)
        futuro = respaldo.stat().st_mtime + 60
        os.utime(self.db, (futuro - 120, futuro - 120))

        self.assertIsNone(respaldar_si_hubo_cambios(self.db, self.carpeta))

    def test_copia_externa_ausente_no_falla_y_queda_pendiente(self):
        crear_bd(self.db, ["dato"])
        configuracion.guardar_ruta_secundaria(str(self.raiz / "usb-que-no-existe"))

        respaldar_completo(self.db, self.carpeta)

        self.assertEqual(configuracion.obtener(configuracion.CLAVE_COPIA_PENDIENTE), "si")

    def test_copia_externa_se_registra_cuando_el_destino_existe(self):
        crear_bd(self.db, ["dato"])
        usb = self.raiz / "usb"
        usb.mkdir()
        configuracion.guardar_ruta_secundaria(str(usb))

        respaldo = respaldar_completo(self.db, self.carpeta)

        self.assertTrue((usb / respaldo.name).exists())
        self.assertIsNotNone(configuracion.ultima_copia_externa())


class RotacionTests(unittest.TestCase):
    def _respaldo(self, dias_antes: float, etiqueta: str = "auto") -> Respaldo:
        fecha = AHORA - timedelta(days=dias_antes)
        return Respaldo(ruta=Path(f"colegio-{dias_antes}-{etiqueta}.db"), fecha=fecha, etiqueta=etiqueta)

    def test_nunca_borra_los_cinco_mas_recientes(self):
        respaldos = sorted((self._respaldo(400 + i * 60) for i in range(8)), key=lambda r: r.fecha, reverse=True)

        conservados = respaldos_a_conservar(respaldos, AHORA)

        self.assertTrue({r.ruta for r in respaldos[:5]}.issubset(conservados))

    def test_conserva_un_respaldo_por_dia_entre_7_y_30_dias(self):
        mismo_dia = [Respaldo(Path(f"hora-{hora}.db"), datetime(2026, 5, 12, hora), "auto") for hora in (8, 12, 20)]
        recientes = [self._respaldo(dias) for dias in (1, 2, 3, 4, 5)]
        todos = sorted(mismo_dia + recientes, key=lambda r: r.fecha, reverse=True)

        conservados = respaldos_a_conservar(todos, AHORA)

        self.assertEqual(len([r for r in mismo_dia if r.ruta in conservados]), 1)

    def test_conserva_un_respaldo_por_mes_para_respaldos_antiguos(self):
        mes_antiguo = [self._respaldo(100), self._respaldo(101)]
        recientes = [self._respaldo(d) for d in (1, 2, 3, 4, 5)]
        todos = sorted(mes_antiguo + recientes, key=lambda r: r.fecha, reverse=True)

        conservados = respaldos_a_conservar(todos, AHORA)

        self.assertEqual(len([r for r in mes_antiguo if r.ruta in conservados]), 1)

    def test_respaldos_antes_de_restaurar_se_protegen_90_dias(self):
        protegido = self._respaldo(60, etiqueta="antes-de-restaurar")
        recientes = [self._respaldo(d) for d in (1, 2, 3, 4, 5)]
        todos = sorted(recientes + [protegido], key=lambda r: r.fecha, reverse=True)

        self.assertIn(protegido.ruta, respaldos_a_conservar(todos, AHORA))


class InstanciaUnicaTests(unittest.TestCase):
    def test_segunda_instancia_es_rechazada(self):
        with socket.socket() as sonda:
            sonda.bind(("127.0.0.1", 0))
            puerto = sonda.getsockname()[1]

        primera = adquirir_bloqueo(puerto)
        try:
            self.assertIsNotNone(primera)
            self.assertIsNone(adquirir_bloqueo(puerto))
        finally:
            primera.close()


class PermisosRespaldosTests(TestCase):
    def test_secretaria_no_accede_a_respaldos_ni_usuarios(self):
        usuario = get_user_model().objects.create_user("secretaria", password="clave-muy-segura-2026", is_staff=True)
        usuario.groups.add(Group.objects.get(name=NOMBRE_SECRETARIA))
        self.client.force_login(usuario)

        self.assertEqual(self.client.get("/respaldos/").status_code, 403)
        self.assertEqual(self.client.get("/auth/user/").status_code, 403)

    def test_directora_accede_a_respaldos(self):
        usuario = get_user_model().objects.create_superuser("directora", "", "clave-muy-segura-2026")
        self.client.force_login(usuario)

        self.assertEqual(self.client.get("/respaldos/").status_code, 200)
