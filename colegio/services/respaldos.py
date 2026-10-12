import os
import re
import shutil
import sqlite3
import zipfile
from io import BytesIO
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path

from django.db import connections

from colegio.services import configuracion

FORMATO_FECHA_ARCHIVO = "%Y%m%d-%H%M%S-%f"
PATRON_NOMBRE = re.compile(r"^colegio-(?P<fecha>\d{8}-\d{6}-\d{6})-(?P<etiqueta>[a-z-]+)\.db$")
ETIQUETAS_PROTEGIDAS = ("antes-de-restaurar", "antes-de-migrar")
ETIQUETA_AUTOMATICA = "auto"
ULTIMOS_PROTEGIDOS = 5
DIAS_COMPLETOS = 7
DIAS_DIARIOS = 30
DIAS_MENSUALES = 24 * 30
DIAS_PROTEGIDOS_ETIQUETA = 90
DIAS_AVISO_COPIA_EXTERNA = 7
DIAS_URGENTE_COPIA_EXTERNA = 30
INTEGRIDAD_OK = "ok"
NOMBRE_BD_EN_PAQUETE = "colegio.db"
NOMBRE_EXCEL_EN_PAQUETE = "colegio_estudiantes.xlsx"
MENSAJE_RESPALDO_INVALIDO = "El respaldo no pasó la verificación de integridad."


class RespaldoInvalido(RuntimeError):
    pass


@dataclass(frozen=True)
class Respaldo:
    ruta: Path
    fecha: datetime
    etiqueta: str


def archivo_sano(ruta: Path) -> bool:
    try:
        conexion = sqlite3.connect(ruta)
        try:
            return conexion.execute("PRAGMA integrity_check").fetchone()[0] == INTEGRIDAD_OK
        finally:
            conexion.close()
    except sqlite3.DatabaseError:
        return False


def respaldar(db: Path, carpeta: Path, etiqueta: str = ETIQUETA_AUTOMATICA, ahora: datetime | None = None) -> Path:
    carpeta.mkdir(parents=True, exist_ok=True)
    marca = (ahora or datetime.now()).strftime(FORMATO_FECHA_ARCHIVO)
    temporal = carpeta / f".tmp-{marca}.db"
    final = carpeta / f"colegio-{marca}-{etiqueta}.db"
    _copiar_con_api_de_respaldo(db, temporal)
    if not archivo_sano(temporal):
        temporal.unlink(missing_ok=True)
        raise RespaldoInvalido(MENSAJE_RESPALDO_INVALIDO)
    temporal.replace(final)
    return final


def _copiar_con_api_de_respaldo(origen: Path, destino: Path) -> None:
    fuente = sqlite3.connect(f"{origen.as_uri()}?mode=ro", uri=True)
    try:
        copia = sqlite3.connect(destino)
        try:
            fuente.backup(copia)
        finally:
            copia.close()
    finally:
        fuente.close()


def listar_respaldos(carpeta: Path) -> list[Respaldo]:
    if not carpeta.exists():
        return []
    respaldos = [_respaldo_desde_archivo(ruta) for ruta in carpeta.iterdir()]
    return sorted((r for r in respaldos if r), key=lambda r: r.fecha, reverse=True)


def _respaldo_desde_archivo(ruta: Path) -> Respaldo | None:
    coincidencia = PATRON_NOMBRE.match(ruta.name)
    if not coincidencia:
        return None
    fecha = datetime.strptime(coincidencia["fecha"], FORMATO_FECHA_ARCHIVO)
    return Respaldo(ruta=ruta, fecha=fecha, etiqueta=coincidencia["etiqueta"])


def respaldos_a_conservar(respaldos: list[Respaldo], ahora: datetime) -> set[Path]:
    """Recibe respaldos del más reciente al más antiguo y devuelve las rutas que se deben conservar."""
    conservados = {r.ruta for r in respaldos[:ULTIMOS_PROTEGIDOS]}
    conservados |= {r.ruta for r in respaldos if _protegido_por_etiqueta(r, ahora)}
    vistas = set()
    for respaldo in respaldos:
        clave = _clave_de_retencion(respaldo.fecha, ahora)
        if clave is None or clave in vistas:
            continue
        vistas.add(clave)
        conservados.add(respaldo.ruta)
    return conservados


def _protegido_por_etiqueta(respaldo: Respaldo, ahora: datetime) -> bool:
    reciente = ahora - respaldo.fecha <= timedelta(days=DIAS_PROTEGIDOS_ETIQUETA)
    return respaldo.etiqueta in ETIQUETAS_PROTEGIDAS and reciente


def _clave_de_retencion(fecha: datetime, ahora: datetime):
    antiguedad = ahora - fecha
    if antiguedad <= timedelta(days=DIAS_COMPLETOS):
        return ("completo", fecha)
    if antiguedad <= timedelta(days=DIAS_DIARIOS):
        return ("dia", fecha.date())
    if antiguedad <= timedelta(days=DIAS_MENSUALES):
        return ("mes", fecha.year, fecha.month)
    return None


def rotar(carpeta: Path, ahora: datetime | None = None) -> list[Path]:
    ahora = ahora or datetime.now()
    respaldos = listar_respaldos(carpeta)
    conservados = respaldos_a_conservar(respaldos, ahora)
    eliminados = [r.ruta for r in respaldos if r.ruta not in conservados]
    for ruta in eliminados:
        ruta.unlink()
    return eliminados


def restaurar(db: Path, respaldo: Path, carpeta: Path) -> None:
    if not archivo_sano(respaldo):
        raise RespaldoInvalido(MENSAJE_RESPALDO_INVALIDO)
    if db.exists():
        respaldar(db, carpeta, etiqueta="antes-de-restaurar")
    connections.close_all()
    temporal = db.with_name(f"{db.name}.restaurando")
    shutil.copyfile(respaldo, temporal)
    os.replace(temporal, db)
    _borrar_journal_huerfano(db)


def _borrar_journal_huerfano(db: Path) -> None:
    db.with_name(f"{db.name}-journal").unlink(missing_ok=True)


def migrar_con_respaldo(db: Path, carpeta: Path, ejecutar_migracion) -> None:
    previo = respaldar(db, carpeta, etiqueta="antes-de-migrar") if db.exists() else None
    try:
        ejecutar_migracion()
    except Exception:
        if previo:
            restaurar(db, previo, carpeta)
        raise


def respaldar_completo(db: Path, carpeta: Path, ahora: datetime | None = None) -> Path:
    momento = ahora or datetime.now()
    respaldo = respaldar(db, carpeta, ahora=momento)
    _copiar_a_ruta_secundaria(respaldo, momento)
    rotar(carpeta, momento)
    return respaldo


def _copiar_a_ruta_secundaria(respaldo: Path, momento: datetime) -> None:
    destino = configuracion.ruta_secundaria()
    if destino is None:
        return
    try:
        shutil.copyfile(respaldo, destino / respaldo.name)
    except OSError:
        configuracion.registrar_copia_externa_pendiente()
        return
    configuracion.registrar_copia_externa_exitosa(momento)


def dias_sin_copia_externa(ahora: datetime) -> int | None:
    ultima = configuracion.ultima_copia_externa()
    return (ahora - ultima).days if ultima else None


def paquete_de_descarga(db: Path, carpeta: Path) -> bytes:
    from colegio.services.exportar_excel import libro_completo

    respaldo = respaldar(db, carpeta, etiqueta="descarga")
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as paquete:
        paquete.write(respaldo, arcname=NOMBRE_BD_EN_PAQUETE)
        paquete.writestr(NOMBRE_EXCEL_EN_PAQUETE, libro_completo())
    return buffer.getvalue()


def nivel_aviso_copia_externa(dias_sin_copia: int | None) -> str | None:
    if dias_sin_copia is None or dias_sin_copia > DIAS_URGENTE_COPIA_EXTERNA:
        return "urgente"
    if dias_sin_copia > DIAS_AVISO_COPIA_EXTERNA:
        return "aviso"
    return None


def respaldar_si_hubo_cambios(db: Path, carpeta: Path) -> Path | None:
    ultimos = listar_respaldos(carpeta)
    if ultimos and db.stat().st_mtime <= ultimos[0].fecha.timestamp():
        return None
    return respaldar_completo(db, carpeta)
