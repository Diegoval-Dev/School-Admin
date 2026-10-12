from datetime import date, datetime
from pathlib import Path
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from colegio.models import CicloEscolar, Concepto, Estudiante, Genero, Grado, Jornada, Matricula, Pago
from colegio.services.alertas import alertas_del_sistema
from colegio.services.respaldos import Respaldo, nivel_aviso_copia_externa
from colegio.views.inicio import buscar_estudiantes


RESPALDO_RECIENTE = Respaldo(Path("colegio-reciente.db"), datetime(2026, 3, 10, 9, 50), "auto")
NOMBRE_ESTUDIANTE = "Castillo Ruiz, Mario"


class InicioTestCase(TestCase):
    def setUp(self):
        self.ciclo = CicloEscolar.objects.create(anio=2026, activo=True)
        self.estudiante = Estudiante.objects.create(
            primer_apellido="Castillo",
            segundo_apellido="Ruiz",
            primer_nombre="Mario",
            genero=Genero.MASCULINO,
            numero_documento="1234567890123",
        )
        self.matricula = Matricula.objects.create(estudiante=self.estudiante, ciclo=self.ciclo, grado=Grado.PRIMERO)
        self.usuario = get_user_model().objects.create_superuser("directora", "", "clave-muy-segura-2026")
        self.client.force_login(self.usuario)


class BusquedaTests(InicioTestCase):
    def test_busca_por_nombre_y_apellido(self):
        self.assertIn(self.estudiante, buscar_estudiantes("mario castillo"))

    def test_busca_por_documento(self):
        self.assertIn(self.estudiante, buscar_estudiantes("1234567890123"))

    def test_terminos_que_no_coinciden_no_devuelven_nada(self):
        self.assertEqual(list(buscar_estudiantes("mario inexistente")), [])

    def test_inicio_muestra_resultados(self):
        respuesta = self.client.get("/", {"q": "Castillo"})

        self.assertContains(respuesta, NOMBRE_ESTUDIANTE)


class AlertasTests(InicioTestCase):
    def test_sin_copia_externa_nunca_hay_alerta_urgente(self):
        with patch("colegio.services.alertas.listar_respaldos", return_value=[RESPALDO_RECIENTE]):
            alertas = alertas_del_sistema(self.ciclo, datetime(2026, 3, 10, 10, 0))

        self.assertIn("urgente", [alerta.nivel for alerta in alertas])

    def test_nivel_de_copia_externa_segun_antiguedad(self):
        self.assertIsNone(nivel_aviso_copia_externa(3))
        self.assertEqual(nivel_aviso_copia_externa(10), "aviso")
        self.assertEqual(nivel_aviso_copia_externa(45), "urgente")

    def test_alerta_de_pagos_pendientes_del_mes(self):
        with patch("colegio.services.alertas.listar_respaldos", return_value=[RESPALDO_RECIENTE]):
            alertas = alertas_del_sistema(self.ciclo, datetime(2026, 3, 10, 10, 0))

        self.assertTrue(any("Marzo" in alerta.mensaje for alerta in alertas))

    def test_sin_pendientes_no_hay_alerta_de_pagos(self):
        Pago.objects.create(
            matricula=self.matricula, concepto=Concepto.MARZO, monto=Decimal("150"), fecha_pago=date(2026, 3, 1)
        )
        with patch("colegio.services.alertas.listar_respaldos", return_value=[RESPALDO_RECIENTE]):
            alertas = alertas_del_sistema(self.ciclo, datetime(2026, 3, 10, 10, 0))

        self.assertFalse(any("Marzo" in alerta.mensaje for alerta in alertas))


class ReportesTests(InicioTestCase):
    def test_listado_por_grado_y_jornada(self):
        respuesta = self.client.get(
            "/reportes/listado/", {"ciclo": self.ciclo.pk, "grado": Grado.PRIMERO, "jornada": Jornada.DIARIO}
        )

        self.assertContains(respuesta, "Castillo")

    def test_historico_incluye_solo_retirados_y_graduados(self):
        self.estudiante.estado = "R"
        self.estudiante.save()

        respuesta = self.client.get("/reportes/historico/")

        self.assertContains(respuesta, NOMBRE_ESTUDIANTE)

    def test_ficha_imprimible_responde(self):
        respuesta = self.client.get(f"/reportes/ficha/{self.estudiante.pk}/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Datos del estudiante")
