from django.contrib import admin
from django.urls import path

from colegio.views.setup import configuracion_inicial

urlpatterns = [
    path("configuracion-inicial/", configuracion_inicial, name="configuracion_inicial"),
    path("", admin.site.urls),
]
