from datetime import datetime

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Q
from django.shortcuts import render

from colegio.models import Estudiante
from colegio.permisos import es_directora
from colegio.services.alertas import alertas_del_sistema
from colegio.views.filtros import ciclo_desde, contexto_admin

PLANTILLA = "colegio/inicio.html"
LIMITE_RESULTADOS = 30
CAMPOS_BUSQUEDA = (
    "codigo",
    "primer_nombre",
    "segundo_nombre",
    "primer_apellido",
    "segundo_apellido",
    "numero_documento",
)


def buscar_estudiantes(texto: str):
    if not texto.strip():
        return Estudiante.objects.none()
    filtro = Q()
    for termino in texto.split():
        filtro &= Q(*[(f"{campo}__icontains", termino) for campo in CAMPOS_BUSQUEDA], _connector=Q.OR)
    return Estudiante.objects.filter(filtro)[:LIMITE_RESULTADOS]


@staff_member_required
def inicio(request):
    ciclo = ciclo_desde(request)
    contexto = contexto_admin(
        request,
        consulta=request.GET.get("q", ""),
        resultados=buscar_estudiantes(request.GET.get("q", "")),
        alertas=alertas_del_sistema(ciclo, datetime.now()),
        ciclo=ciclo,
        es_directora=es_directora(request.user),
        version=settings.VERSION,
    )
    return render(request, PLANTILLA, contexto)
