from django.utils import timezone

PREFIJO_DOCENTE = "D-"
FORMATO_ESTUDIANTE = "{anio}-{numero:04d}"
FORMATO_DOCENTE = PREFIJO_DOCENTE + "{numero:03d}"


def _siguiente_secuencia(codigos_existentes, prefijo: str) -> int:
    sufijos = (codigo.removeprefix(prefijo) for codigo in codigos_existentes)
    numeros = [int(sufijo) for sufijo in sufijos if sufijo.isdigit()]
    return max(numeros, default=0) + 1


def siguiente_codigo_estudiante(anio: int | None = None) -> str:
    from colegio.models import Estudiante

    anio = anio or timezone.localdate().year
    prefijo = f"{anio}-"
    existentes = Estudiante.objects.filter(codigo__startswith=prefijo).values_list("codigo", flat=True)
    return FORMATO_ESTUDIANTE.format(anio=anio, numero=_siguiente_secuencia(existentes, prefijo))


def siguiente_codigo_docente() -> str:
    from colegio.models import Docente

    existentes = Docente.objects.filter(codigo__startswith=PREFIJO_DOCENTE).values_list("codigo", flat=True)
    return FORMATO_DOCENTE.format(numero=_siguiente_secuencia(existentes, PREFIJO_DOCENTE))
