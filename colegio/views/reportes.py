from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render

from colegio.models import EstadoEstudiante, Estudiante, Grado, Jornada, Matricula
from colegio.views.filtros import ciclo_desde, contexto_admin, filtros_de_grado

PLANTILLA_LISTADO = "colegio/reportes/listado.html"
PLANTILLA_HISTORICO = "colegio/reportes/historico.html"
PLANTILLA_FICHA = "colegio/reportes/ficha.html"
ESTADOS_HISTORICOS = (EstadoEstudiante.RETIRADO, EstadoEstudiante.GRADUADO)


def _textos_de_encabezado(filtros: dict) -> dict:
    return {
        "grado_texto": Grado(filtros["grado"]).label,
        "jornada_texto": Jornada(filtros["jornada"]).label,
    }


@staff_member_required
def listado_estudiantes(request):
    filtros = filtros_de_grado(request)
    matriculas = []
    if filtros["ciclo"]:
        matriculas = (
            Matricula.objects.filter(ciclo=filtros["ciclo"], grado=filtros["grado"], jornada=filtros["jornada"], activa=True)
            .select_related("estudiante")
            .order_by("estudiante__primer_apellido", "estudiante__primer_nombre")
        )
    contexto = {**filtros, **_textos_de_encabezado(filtros), "matriculas": matriculas}
    return render(request, PLANTILLA_LISTADO, contexto)


@staff_member_required
def estudiantes_historicos(request):
    estudiantes = Estudiante.objects.filter(estado__in=ESTADOS_HISTORICOS).prefetch_related("matriculas__ciclo")
    return render(request, PLANTILLA_HISTORICO, contexto_admin(request, estudiantes=estudiantes))


@staff_member_required
def ficha_estudiante(request, estudiante_id: int):
    estudiante = get_object_or_404(
        Estudiante.objects.prefetch_related("responsables", "contactos", "direcciones", "matriculas__ciclo"),
        pk=estudiante_id,
    )
    return render(request, PLANTILLA_FICHA, {"estudiante": estudiante, "ciclo": ciclo_desde(request)})
