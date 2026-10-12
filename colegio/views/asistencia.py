from datetime import date
from urllib.parse import urlencode

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from colegio.models import CicloEscolar, EstadoAsistencia, Grado, Jornada, Matricula
from colegio.services.asistencia import ciclar_asistencia, dias_del_mes, es_fin_de_semana, filas_de_asistencia
from colegio.services.exportar_excel import libro_asistencia
from colegio.views.filtros import contexto_admin, filtros_de_grado

PLANTILLA_TABLA = "colegio/asistencia/tabla.html"
PLANTILLA_REPORTE = "colegio/asistencia/reporte.html"
TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
SEPARADOR_CELDA = "|"
MESES = [
    (1, "Enero"), (2, "Febrero"), (3, "Marzo"), (4, "Abril"), (5, "Mayo"), (6, "Junio"),
    (7, "Julio"), (8, "Agosto"), (9, "Septiembre"), (10, "Octubre"), (11, "Noviembre"), (12, "Diciembre"),
]
SIMBOLOS = {
    EstadoAsistencia.PRESENTE: "✓",
    EstadoAsistencia.AUSENTE: "✗",
    EstadoAsistencia.EXCUSA: "E",
}


def _mes_desde(request) -> int:
    return int(request.GET.get("mes", timezone.localdate().month))


def _datos_de_mes(request) -> dict:
    filtros = filtros_de_grado(request)
    if not filtros["ciclo"]:
        return {**filtros, "mes": None, "dias": [], "filas": []}
    mes = _mes_desde(request)
    dias = dias_del_mes(filtros["ciclo"].anio, mes, filtros["jornada"])
    matriculas = _matriculas_activas(filtros)
    return {
        **filtros,
        "mes": mes,
        "dias": [{"fecha": dia, "fin_de_semana": es_fin_de_semana(dia)} for dia in dias],
        "filas": _con_simbolos(filas_de_asistencia(matriculas, dias)),
    }


def _con_simbolos(filas: list[dict]) -> list[dict]:
    for fila in filas:
        fila["celdas"] = [(fecha, estado, SIMBOLOS.get(estado, "")) for fecha, estado in fila["celdas"]]
    return filas


def _matriculas_activas(filtros: dict):
    return (
        Matricula.objects.filter(
            ciclo=filtros["ciclo"], grado=filtros["grado"], jornada=filtros["jornada"], activa=True
        )
        .select_related("estudiante")
        .order_by("estudiante__primer_apellido", "estudiante__primer_nombre")
    )


@staff_member_required
def asistencia_tabla(request):
    contexto = contexto_admin(
        request,
        **_datos_de_mes(request),
        grados=Grado.choices,
        jornadas=Jornada.choices,
        ciclos=CicloEscolar.objects.all(),
        meses=MESES,
    )
    return render(request, PLANTILLA_TABLA, contexto)


@staff_member_required
def asistencia_ciclar(request):
    if request.method != "POST":
        raise Http404("Método no permitido.")
    matricula_id, fecha = _celda_desde(request.POST.get("celda", ""))
    matricula = get_object_or_404(Matricula, pk=matricula_id)
    try:
        ciclar_asistencia(matricula, fecha)
    except ValidationError:
        raise Http404("La matrícula no está activa.")
    query = urlencode(
        {"ciclo": matricula.ciclo_id, "grado": matricula.grado, "jornada": matricula.jornada, "mes": fecha.month}
    )
    return redirect(f"{reverse('asistencia_tabla')}?{query}")


@staff_member_required
def asistencia_reporte(request):
    contexto = _datos_de_mes(request)
    contexto["grado_texto"] = Grado(contexto["grado"]).label
    contexto["jornada_texto"] = Jornada(contexto["jornada"]).label
    contexto["mes_texto"] = MESES[contexto["mes"] - 1][1] if contexto["mes"] else ""
    return render(request, PLANTILLA_REPORTE, contexto)


@staff_member_required
def asistencia_excel(request):
    datos = _datos_de_mes(request)
    respuesta = HttpResponse(
        libro_asistencia(datos["filas"], [dia["fecha"] for dia in datos["dias"]]),
        content_type=TIPO_EXCEL,
    )
    respuesta["Content-Disposition"] = f'attachment; filename="asistencia-{datos["grado"]}-{datos["mes"]}.xlsx"'
    return respuesta


def _celda_desde(valor: str) -> tuple[int, date]:
    try:
        matricula_id, fecha_iso = valor.split(SEPARADOR_CELDA)
        return int(matricula_id), date.fromisoformat(fecha_iso)
    except ValueError:
        raise Http404("Celda inválida.")
