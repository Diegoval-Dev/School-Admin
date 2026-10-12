from django.shortcuts import redirect
from django.urls import reverse

from colegio.services.usuarios import hay_usuarios

RUTAS_SIN_CONFIGURAR = ("/configuracion-inicial/", "/static/")


class ConfiguracionInicialMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._requiere_configuracion(request):
            return redirect(reverse("configuracion_inicial"))
        return self.get_response(request)

    def _requiere_configuracion(self, request):
        if request.path.startswith(RUTAS_SIN_CONFIGURAR):
            return False
        return not hay_usuarios()
