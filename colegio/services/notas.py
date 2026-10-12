from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction

from colegio.models import Grado, Materia, Matricula, Nota

PROMEDIO_DECIMALES = Decimal("0.01")
MENSAJE_PUNTEO_INVALIDO = "El punteo de {etiqueta} no es un número válido."


def filas_de_notas(ciclo, grado: str, materia: Materia) -> list[dict]:
    matriculas = (
        Matricula.objects.filter(ciclo=ciclo, grado=grado, activa=True)
        .select_related("estudiante")
        .order_by("estudiante__primer_apellido", "estudiante__primer_nombre")
    )
    punteos = {
        (nota.matricula_id, nota.unidad): nota.punteo
        for nota in Nota.objects.filter(matricula__in=matriculas, materia=materia)
    }
    return [_fila_de_notas(matricula, punteos) for matricula in matriculas]


def _fila_de_notas(matricula: Matricula, punteos: dict) -> dict:
    unidades = [
        (unidad, punteos.get((matricula.pk, unidad)))
        for unidad in range(1, settings.UNIDADES_POR_CICLO + 1)
    ]
    entregadas = [punteo for _, punteo in unidades if punteo is not None]
    total = sum(entregadas, Decimal("0"))
    promedio = (total / len(entregadas)).quantize(PROMEDIO_DECIMALES) if entregadas else None
    return {"matricula": matricula, "unidades": unidades, "total": total if entregadas else None, "promedio": promedio}


def guardar_punteos(materia: Materia, punteos: dict[tuple[int, int], str]) -> None:
    """Guarda todas las celdas no vacías en una sola transacción; si una falla, no se guarda ninguna."""
    with transaction.atomic():
        for (matricula_id, unidad), valor in punteos.items():
            if valor.strip():
                _guardar_punteo(materia, matricula_id, unidad, valor.strip())


def _guardar_punteo(materia: Materia, matricula_id: int, unidad: int, valor: str) -> None:
    matricula = Matricula.objects.get(pk=matricula_id)
    nota = Nota.objects.filter(matricula=matricula, materia=materia, unidad=unidad).first()
    nota = nota or Nota(matricula=matricula, materia=materia, unidad=unidad)
    nota.punteo = _punteo_desde_texto(valor, f"la unidad {unidad}")
    nota.full_clean()
    nota.save()


def _punteo_desde_texto(valor: str, etiqueta: str) -> Decimal:
    try:
        punteo = Decimal(valor)
    except InvalidOperation:
        punteo = None
    if punteo is None or not punteo.is_finite():
        raise ValidationError(MENSAJE_PUNTEO_INVALIDO.format(etiqueta=etiqueta))
    return punteo
