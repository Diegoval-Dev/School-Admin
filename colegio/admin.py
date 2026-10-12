from django.contrib import admin
from simple_history.admin import SimpleHistoryAdmin
from unfold.admin import ModelAdmin, TabularInline

from colegio.models import (
    Asignacion,
    CicloEscolar,
    Contacto,
    Direccion,
    Docente,
    Estudiante,
    Materia,
    Matricula,
    Responsable,
)

MAX_RESPONSABLES = 3


class SinBorradoFisicoMixin:
    def has_delete_permission(self, request, obj=None):
        return False


class ResponsableInline(TabularInline):
    model = Responsable
    extra = 0
    max_num = MAX_RESPONSABLES


class ContactoInline(TabularInline):
    model = Contacto
    extra = 1


class DireccionInline(TabularInline):
    model = Direccion
    extra = 1


class MatriculaInline(SinBorradoFisicoMixin, TabularInline):
    model = Matricula
    extra = 0
    fields = ("ciclo", "grado", "jornada", "activa")


class AsignacionInline(SinBorradoFisicoMixin, TabularInline):
    model = Asignacion
    extra = 0


@admin.register(Estudiante)
class EstudianteAdmin(SinBorradoFisicoMixin, ModelAdmin, SimpleHistoryAdmin):
    list_display = ("nombre_completo", "codigo", "edad_display", "estado")
    list_filter = ("estado", "matriculas__grado", "matriculas__jornada", "matriculas__ciclo")
    search_fields = (
        "codigo",
        "primer_nombre",
        "segundo_nombre",
        "primer_apellido",
        "segundo_apellido",
        "numero_documento",
    )
    inlines = (ResponsableInline, ContactoInline, DireccionInline, MatriculaInline)

    @admin.display(description="Edad")
    def edad_display(self, obj):
        return obj.edad if obj.edad is not None else "—"


@admin.register(Docente)
class DocenteAdmin(SinBorradoFisicoMixin, ModelAdmin, SimpleHistoryAdmin):
    list_display = ("nombre_completo", "codigo", "tipo", "activo")
    list_filter = ("tipo", "activo")
    search_fields = ("codigo", "primer_nombre", "primer_apellido", "numero_documento")
    inlines = (AsignacionInline,)


@admin.register(Materia)
class MateriaAdmin(ModelAdmin):
    list_display = ("nombre", "grado", "codigo")
    list_filter = ("grado",)
    search_fields = ("codigo", "nombre")


@admin.register(CicloEscolar)
class CicloEscolarAdmin(ModelAdmin):
    list_display = ("anio", "activo")

    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        if obj.activo:
            CicloEscolar.objects.exclude(pk=obj.pk).update(activo=False)
