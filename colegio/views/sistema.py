from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse

from colegio.services.sistema import cerrar_servidor_despues

RETRASO_CIERRE_SEGUNDOS = 1.0
MENSAJE_CERRADO = "El sistema se está cerrando. Puedes cerrar esta pestaña."


@staff_member_required
def cerrar_sistema(request):
    if request.method != "POST":
        return HttpResponse(status=405)
    cerrar_servidor_despues(RETRASO_CIERRE_SEGUNDOS)
    return HttpResponse(MENSAJE_CERRADO)
