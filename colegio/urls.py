from django.urls import path

from colegio.views import asistencia, pagos

urlpatterns = [
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
