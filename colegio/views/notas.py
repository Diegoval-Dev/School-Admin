from urllib.parse import urlencode

from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from colegio.models import CicloEscolar, Docente, Grado, Materia
from colegio.services.exportar_excel import libro_calificaciones
from colegio.services.notas import filas_de_notas, guardar_punteos
from colegio.views.filtros import ciclo_desde, contexto_admin

PLANTILLA_TABLA = "colegio/notas/tabla.html"
PLANTILLA_REPORTE = "colegio/notas/reporte.html"
TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PREFIJO_CAMPO = "punteo_"
SEPARADOR_CAMPO = "_"
MENSAJE_GUARDADO = "Notas guardadas."


def _datos_de_notas(request) -> dict:
    ciclo = ciclo_desde(request)
    grado = request.GET.get("grado", Grado.PRIMERO)
    materia = _materia_desde(request, grado)
    docente = Docente.objects.filter(pk=request.GET.get("docente")).first()
    filas = filas_de_notas(ciclo, grado, materia) if ciclo and materia else []
    return {
        "ciclo": ciclo,
        "grado": grado,
        "materia": materia,
        "docente": docente,
        "filas": filas,
        "unidades": range(1, settings.UNIDADES_POR_CICLO + 1),
        "fecha": timezone.localdate(),
        "query": _query_de_filtros(ciclo, grado, materia, docente),
    }


def _query_de_filtros(ciclo, grado: str, materia, docente) -> str:
    return urlencode(
        {
            "ciclo": ciclo.pk if ciclo else "",
            "grado": grado,
            "materia": materia.pk if materia else "",
            "docente": docente.pk if docente else "",
        }
    )


def _materia_desde(request, grado: str) -> Materia | None:
    pk = request.GET.get("materia")
    materias = Materia.objects.filter(grado=grado)
    return materias.filter(pk=pk).first() or materias.first()


@staff_member_required
def notas_tabla(request):
    datos = _datos_de_notas(request)
    contexto = contexto_admin(
        request,
        **datos,
        grados=Grado.choices,
        materias=Materia.objects.filter(grado=datos["grado"]),
        docentes=Docente.objects.filter(activo=True),
        ciclos=CicloEscolar.objects.all(),
        nota_aprobacion=settings.NOTA_APROBACION,
        nota_min=settings.NOTA_MIN,
        nota_max=settings.NOTA_MAX,
    )
    return render(request, PLANTILLA_TABLA, contexto)


@staff_member_required
def notas_guardar(request):
    if request.method != "POST":
        raise Http404("Método no permitido.")
    datos = _datos_de_notas(request)
    if not datos["materia"]:
        raise Http404("No hay materia seleccionada.")
    try:
        guardar_punteos(datos["materia"], _punteos_desde_formulario(request.POST))
    except ValidationError as error:
        for mensaje in error.messages:
            messages.error(request, mensaje)
    else:
        messages.success(request, MENSAJE_GUARDADO)
    return redirect(f"{reverse('notas_tabla')}?{request.GET.urlencode()}")


def _punteos_desde_formulario(post) -> dict[tuple[int, int], str]:
    punteos = {}
    for campo, valor in post.items():
        if campo.startswith(PREFIJO_CAMPO):
            matricula_id, unidad = campo[len(PREFIJO_CAMPO):].split(SEPARADOR_CAMPO)
            punteos[(int(matricula_id), int(unidad))] = valor
    return punteos


@staff_member_required
def notas_reporte(request):
    datos = _datos_de_notas(request)
    contexto = {
        **datos,
        "grado_texto": Grado(datos["grado"]).label,
        "jornada_texto": "Todas las jornadas",
    }
    return render(request, PLANTILLA_REPORTE, contexto)


@staff_member_required
def notas_excel(request):
    datos = _datos_de_notas(request)
    respuesta = HttpResponse(
        libro_calificaciones(datos["filas"], settings.UNIDADES_POR_CICLO), content_type=TIPO_EXCEL
    )
    respuesta["Content-Disposition"] = f'attachment; filename="calificaciones-{datos["grado"]}.xlsx"'
    return respuesta
