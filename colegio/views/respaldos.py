from datetime import datetime
from pathlib import Path

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import reverse

from colegio.permisos import solo_directora
from colegio.services import configuracion
from colegio.services.exportar_excel import libro_completo
from colegio.services.respaldos import (
    dias_sin_copia_externa,
    listar_respaldos,
    nivel_aviso_copia_externa,
    listar_respaldos,
    paquete_de_descarga,
    respaldar_completo,
)
from colegio.views.filtros import contexto_admin
from config.paths import get_backup_dir

PLANTILLA = "colegio/respaldos/tabla.html"
TIPO_ZIP = "application/zip"
TIPO_EXCEL = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
MENSAJE_RESPALDO_CREADO = "Respaldo creado correctamente."
MENSAJE_RUTA_GUARDADA = "Ruta secundaria guardada."


def _ruta_db() -> Path:
    return Path(settings.DATABASES["default"]["NAME"])


@solo_directora
def respaldos_tabla(request):
    dias = dias_sin_copia_externa(datetime.now())
    contexto = contexto_admin(
        request,
        respaldos=listar_respaldos(get_backup_dir())[:50],
        ruta_secundaria=configuracion.ruta_secundaria() or "",
        ultima_copia_externa=configuracion.ultima_copia_externa(),
        copia_pendiente=configuracion.obtener(configuracion.CLAVE_COPIA_PENDIENTE) == "si",
        nivel_aviso=nivel_aviso_copia_externa(dias),
        dias_sin_copia=dias,
    )
    return render(request, PLANTILLA, contexto)


@solo_directora
def respaldos_crear(request):
    if request.method == "POST":
        respaldar_completo(_ruta_db(), get_backup_dir())
        messages.success(request, MENSAJE_RESPALDO_CREADO)
    return redirect(reverse("respaldos_tabla"))


@solo_directora
def respaldos_ruta(request):
    if request.method == "POST":
        configuracion.guardar_ruta_secundaria(request.POST.get("ruta", ""))
        messages.success(request, MENSAJE_RUTA_GUARDADA)
    return redirect(reverse("respaldos_tabla"))


@solo_directora
def respaldos_descargar(request):
    contenido = paquete_de_descarga(_ruta_db(), get_backup_dir())
    respuesta = HttpResponse(contenido, content_type=TIPO_ZIP)
    respuesta["Content-Disposition"] = 'attachment; filename="respaldo-colegio.zip"'
    return respuesta


@solo_directora
def respaldos_excel(request):
    respuesta = HttpResponse(libro_completo(), content_type=TIPO_EXCEL)
    respuesta["Content-Disposition"] = 'attachment; filename="colegio_estudiantes.xlsx"'
    return respuesta
