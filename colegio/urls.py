from django.urls import path

from colegio.views import asistencia, inicio, notas, pagos, reportes, respaldos

urlpatterns = [
    path("", inicio.inicio, name="inicio"),
    path("reportes/listado/", reportes.listado_estudiantes, name="reporte_listado"),
    path("reportes/historico/", reportes.estudiantes_historicos, name="reporte_historico"),
    path("reportes/ficha/<int:estudiante_id>/", reportes.ficha_estudiante, name="reporte_ficha"),
    path("respaldos/", respaldos.respaldos_tabla, name="respaldos_tabla"),
    path("respaldos/crear/", respaldos.respaldos_crear, name="respaldos_crear"),
    path("respaldos/ruta/", respaldos.respaldos_ruta, name="respaldos_ruta"),
    path("respaldos/descargar/", respaldos.respaldos_descargar, name="respaldos_descargar"),
    path("respaldos/excel/", respaldos.respaldos_excel, name="respaldos_excel"),
    path("notas/", notas.notas_tabla, name="notas_tabla"),
    path("notas/guardar/", notas.notas_guardar, name="notas_guardar"),
    path("notas/reporte/", notas.notas_reporte, name="notas_reporte"),
    path("notas/excel/", notas.notas_excel, name="notas_excel"),
    path("asistencia/", asistencia.asistencia_tabla, name="asistencia_tabla"),
    path("asistencia/ciclar/", asistencia.asistencia_ciclar, name="asistencia_ciclar"),
    path("asistencia/reporte/", asistencia.asistencia_reporte, name="asistencia_reporte"),
    path("asistencia/excel/", asistencia.asistencia_excel, name="asistencia_excel"),
    path("pagos/", pagos.pagos_tabla, name="pagos_tabla"),
    path("pagos/reporte/", pagos.pagos_reporte, name="pagos_reporte"),
    path("pagos/excel/", pagos.pagos_excel, name="pagos_excel"),
    path("pagos/pendientes/", pagos.pagos_pendientes, name="pagos_pendientes"),
    path("pagos/registrar/<int:matricula_id>/<str:concepto>/", pagos.pago_registrar, name="pago_registrar"),
    path("pagos/anular/<int:pago_id>/", pagos.pago_anular, name="pago_anular"),
    path("pagos/cuenta/<int:matricula_id>/", pagos.estado_cuenta, name="estado_cuenta"),
]
