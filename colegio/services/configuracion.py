import configparser
from datetime import datetime
from pathlib import Path

from config.paths import get_data_dir

NOMBRE_ARCHIVO = "config.ini"
SECCION_RESPALDOS = "respaldos"
CLAVE_RUTA_SECUNDARIA = "ruta_secundaria"
CLAVE_ULTIMA_COPIA_EXTERNA = "ultima_copia_externa"
CLAVE_COPIA_PENDIENTE = "copia_externa_pendiente"
FORMATO_FECHA_CONFIG = "%Y-%m-%d %H:%M:%S"


def _ruta_archivo() -> Path:
    return get_data_dir() / NOMBRE_ARCHIVO


def _leer() -> configparser.ConfigParser:
    parser = configparser.ConfigParser()
    parser.read(_ruta_archivo(), encoding="utf-8")
    if SECCION_RESPALDOS not in parser:
        parser[SECCION_RESPALDOS] = {}
    return parser


def _escribir(parser: configparser.ConfigParser) -> None:
    with _ruta_archivo().open("w", encoding="utf-8") as archivo:
        parser.write(archivo)


def obtener(clave: str, por_defecto: str = "") -> str:
    return _leer()[SECCION_RESPALDOS].get(clave, por_defecto)


def guardar(clave: str, valor: str) -> None:
    parser = _leer()
    parser[SECCION_RESPALDOS][clave] = valor
    _escribir(parser)


def ruta_secundaria() -> Path | None:
    ruta = obtener(CLAVE_RUTA_SECUNDARIA)
    return Path(ruta) if ruta else None


def guardar_ruta_secundaria(ruta: str) -> None:
    guardar(CLAVE_RUTA_SECUNDARIA, ruta.strip())


def registrar_copia_externa_exitosa(momento: datetime) -> None:
    guardar(CLAVE_ULTIMA_COPIA_EXTERNA, momento.strftime(FORMATO_FECHA_CONFIG))
    guardar(CLAVE_COPIA_PENDIENTE, "no")


def registrar_copia_externa_pendiente() -> None:
    guardar(CLAVE_COPIA_PENDIENTE, "si")


def ultima_copia_externa() -> datetime | None:
    valor = obtener(CLAVE_ULTIMA_COPIA_EXTERNA)
    return datetime.strptime(valor, FORMATO_FECHA_CONFIG) if valor else None
