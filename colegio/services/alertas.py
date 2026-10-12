from dataclasses import dataclass
from datetime import datetime, timedelta

from colegio.models import Concepto
from colegio.services.pagos import matriculas_pendientes
from colegio.services.respaldos import dias_sin_copia_externa, listar_respaldos, nivel_aviso_copia_externa
from config.paths import get_backup_dir

PRIMER_MES_COBRO = 1
ULTIMO_MES_COBRO = 10
HORAS_RESPALDO_LOCAL = 24


@dataclass(frozen=True)
class Alerta:
    nivel: str
    mensaje: str


def alertas_del_sistema(ciclo, ahora: datetime) -> list[Alerta]:
    alertas = [
        *_alertas_de_respaldo(ahora),
        *_alertas_de_pagos(ciclo, ahora),
    ]
    return [alerta for alerta in alertas if alerta]


def _alertas_de_respaldo(ahora: datetime) -> list[Alerta | None]:
    ultimo_local = listar_respaldos(get_backup_dir())
    alerta_local = None
    if not ultimo_local or ahora - ultimo_local[0].fecha > timedelta(hours=HORAS_RESPALDO_LOCAL):
        alerta_local = Alerta("aviso", "No hay un respaldo reciente del sistema. Abre Respaldos y crea uno.")
    nivel = nivel_aviso_copia_externa(dias_sin_copia_externa(ahora))
    alerta_externa = _alerta_copia_externa(nivel)
    return [alerta_local, alerta_externa]


def _alerta_copia_externa(nivel: str | None) -> Alerta | None:
    if nivel is None:
        return None
    return Alerta(nivel, "Copia tu respaldo a la USB: hace tiempo que no se copia fuera de esta PC.")


def _alertas_de_pagos(ciclo, ahora: datetime) -> list[Alerta | None]:
    if ciclo is None or not PRIMER_MES_COBRO <= ahora.month <= ULTIMO_MES_COBRO:
        return []
    concepto = Concepto.values[ahora.month]
    pendientes = matriculas_pendientes(ciclo, concepto).count()
    if not pendientes:
        return []
    etiqueta = Concepto(concepto).label
    return [Alerta("aviso", f"{pendientes} estudiante(s) sin pago de {etiqueta}.")]
