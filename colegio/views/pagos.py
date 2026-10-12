from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from colegio.forms import AnulacionPagoForm, PagoForm
from colegio.models import CicloEscolar, Concepto, Grado, Jornada, Matricula, Pago
from colegio.services.exportar_excel import libro_pagos
from colegio.views.filtros import ciclo_desde, contexto_admin, filtros_de_grado
from colegio.services.pagos import (
    anular_pago,
    filas_de_pagos,
    matriculas_pendientes,
    registrar_pago,
    total_pagado,
)

PLANTILLA_TABLA = "colegio/pagos/tabla.html"
PLANTILLA_REGISTRAR = "colegio/pagos/registrar.html"
PLANTILLA_ANULAR = "colegio/pagos/anular.html"
PLANTILLA_ESTADO_CUENTA = "colegio/pagos/estado_cuenta.html"
PLANTILLA_PENDIENTES = "colegio/pagos/pendientes.html"
PLANTILLA_REPORTE = "colegio/pagos/reporte.html"
TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def _filtros_con_filas(request) -> dict:
    filtros = filtros_de_grado(request)
    filas = filas_de_pagos(filtros["ciclo"], filtros["grado"], filtros["jornada"]) if filtros["ciclo"] else []
    return {**filtros, "filas": filas}


@staff_member_required
def pagos_tabla(request):
    contexto = contexto_admin(
        request,
        **_filtros_con_filas(request),
        grados=Grado.choices,
        jornadas=Jornada.choices,
        ciclos=CicloEscolar.objects.all(),
        conceptos=Concepto.choices,
    )
    return render(request, PLANTILLA_TABLA, contexto)


@staff_member_required
def pagos_reporte(request):
    filtros = _filtros_con_filas(request)
    contexto = {
        **filtros,
        "conceptos": Concepto.choices,
        "grado_texto": Grado(filtros["grado"]).label,
        "jornada_texto": Jornada(filtros["jornada"]).label,
    }
    return render(request, PLANTILLA_REPORTE, contexto)


@staff_member_required
def pagos_excel(request):
    filtros = _filtros_con_filas(request)
    respuesta = HttpResponse(libro_pagos(filtros["filas"]), content_type=TIPO_EXCEL)
    respuesta["Content-Disposition"] = f'attachment; filename="pagos-{filtros["grado"]}-{filtros["jornada"]}.xlsx"'
    return respuesta


@staff_member_required
def pago_registrar(request, matricula_id: int, concepto: str):
    matricula = get_object_or_404(Matricula.objects.select_related("estudiante"), pk=matricula_id)
    if concepto not in Concepto.values:
        raise Http404("Concepto inválido.")
    formulario = PagoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            registrar_pago(matricula, concepto, **formulario.cleaned_data)
        except ValidationError as error:
            formulario.add_error(None, error)
        else:
            return redirect(_url_tabla(matricula))
    contexto = contexto_admin(
        request, matricula=matricula, concepto=Concepto(concepto), formulario=formulario
    )
    return render(request, PLANTILLA_REGISTRAR, contexto)


@staff_member_required
def pago_anular(request, pago_id: int):
    pago = get_object_or_404(Pago.objects.select_related("matricula__estudiante"), pk=pago_id)
    formulario = AnulacionPagoForm(request.POST or None)
    if request.method == "POST" and formulario.is_valid():
        try:
            anular_pago(pago, formulario.cleaned_data["motivo"])
        except ValidationError as error:
            formulario.add_error(None, error)
        else:
            return redirect("estado_cuenta", matricula_id=pago.matricula_id)
    contexto = contexto_admin(request, pago=pago, formulario=formulario)
    return render(request, PLANTILLA_ANULAR, contexto)


@staff_member_required
def estado_cuenta(request, matricula_id: int):
    matricula = get_object_or_404(Matricula.objects.select_related("estudiante", "ciclo"), pk=matricula_id)
    contexto = contexto_admin(
        request,
        matricula=matricula,
        pagos=matricula.pagos.all(),
        total=total_pagado(matricula),
    )
    return render(request, PLANTILLA_ESTADO_CUENTA, contexto)


@staff_member_required
def pagos_pendientes(request):
    ciclo = ciclo_desde(request)
    concepto = request.GET.get("concepto", Concepto.ENERO)
    matriculas = matriculas_pendientes(ciclo, concepto) if ciclo else []
    contexto = contexto_admin(
        request,
        ciclo=ciclo,
        concepto=Concepto(concepto),
        matriculas=matriculas,
        ciclos=CicloEscolar.objects.all(),
        conceptos=Concepto.choices,
    )
    return render(request, PLANTILLA_PENDIENTES, contexto)


def _url_tabla(matricula: Matricula) -> str:
    query = f"ciclo={matricula.ciclo_id}&grado={matricula.grado}&jornada={matricula.jornada}"
    return f"{reverse('pagos_tabla')}?{query}"
