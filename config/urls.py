from django.contrib import admin
from django.urls import include, path

from colegio.views.setup import configuracion_inicial

urlpatterns = [
    path("configuracion-inicial/", configuracion_inicial, name="configuracion_inicial"),
    path("", include("colegio.urls")),
    path("", admin.site.urls),
]
