from django.contrib import admin

from colegio.models import CicloEscolar, Grado, Jornada


def ciclo_desde(request):
    pk = request.GET.get("ciclo")
    if pk:
        return CicloEscolar.objects.filter(pk=pk).first()
    return CicloEscolar.objects.filter(activo=True).first()


def filtros_de_grado(request) -> dict:
    return {
        "ciclo": ciclo_desde(request),
        "grado": request.GET.get("grado", Grado.PRIMERO),
        "jornada": request.GET.get("jornada", Jornada.DIARIO),
    }


def contexto_admin(request, **extra) -> dict:
    return {**admin.site.each_context(request), **extra}
