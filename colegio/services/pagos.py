from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db.models import Sum

from colegio.models import Concepto, Matricula, Pago

TOTAL_CERO = Decimal("0.00")
MENSAJE_PAGO_DUPLICADO = "Ya existe un pago vigente para este concepto. Anúlalo primero si fue un error."
MENSAJE_MOTIVO_REQUERIDO = "Indica el motivo de la anulación."


def pago_vigente(matricula: Matricula, concepto: str) -> Pago | None:
    return Pago.objects.filter(matricula=matricula, concepto=concepto, anulado=False).first()


def registrar_pago(matricula: Matricula, concepto: str, **datos) -> Pago:
    if pago_vigente(matricula, concepto):
        raise ValidationError(MENSAJE_PAGO_DUPLICADO)
    pago = Pago(matricula=matricula, concepto=concepto, **datos)
    pago.full_clean()
    pago.save()
    return pago


def anular_pago(pago: Pago, motivo: str) -> None:
    motivo_limpio = motivo.strip()
    if not motivo_limpio:
        raise ValidationError(MENSAJE_MOTIVO_REQUERIDO)
    pago.anulado = True
    pago.motivo_anulacion = motivo_limpio
    pago.save()


def total_pagado(matricula: Matricula) -> Decimal:
    total = Pago.objects.filter(matricula=matricula, anulado=False).aggregate(total=Sum("monto"))["total"]
    return total or TOTAL_CERO


def filas_de_pagos(ciclo, grado: str, jornada: str) -> list[dict]:
    matriculas = (
        Matricula.objects.filter(ciclo=ciclo, grado=grado, jornada=jornada, activa=True)
        .select_related("estudiante")
        .prefetch_related("pagos")
    )
    return [_fila_de_pagos(matricula) for matricula in matriculas]


def _fila_de_pagos(matricula: Matricula) -> dict:
    vigentes = {pago.concepto: pago for pago in matricula.pagos.all() if not pago.anulado}
    return {
        "matricula": matricula,
        "celdas": [(concepto, vigentes.get(concepto)) for concepto in Concepto.values],
    }


def matriculas_pendientes(ciclo, concepto: str):
    pagadas = Pago.objects.filter(concepto=concepto, anulado=False).values("matricula_id")
    return (
        Matricula.objects.filter(ciclo=ciclo, activa=True)
        .exclude(pk__in=pagadas)
        .select_related("estudiante")
    )
