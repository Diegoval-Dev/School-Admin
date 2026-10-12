from django.contrib.auth.models import Group, Permission

from colegio.models import Asignacion, Asistencia, CicloEscolar, Contacto, Direccion, Docente
from colegio.models import Estudiante, Materia, Matricula, Nota, Pago, Responsable

NOMBRE_DIRECTORA = "Directora"
NOMBRE_SECRETARIA = "Secretaria"
MODELOS_OPERATIVOS = [
    Estudiante, Responsable, Contacto, Direccion, Docente, Asignacion,
    Materia, CicloEscolar, Matricula, Pago, Asistencia, Nota,
]
ACCIONES_SECRETARIA = ("add", "change", "view")


def _permisos_de_modelo(modelo, acciones):
    codenames = [f"{accion}_{modelo._meta.model_name}" for accion in acciones]
    return Permission.objects.filter(
        content_type__app_label=modelo._meta.app_label, codename__in=codenames
    )


def _permisos_secretaria():
    permisos = Permission.objects.none()
    for modelo in MODELOS_OPERATIVOS:
        permisos = permisos | _permisos_de_modelo(modelo, ACCIONES_SECRETARIA)
    return permisos


def crear_grupos_por_defecto() -> None:
    directora, _ = Group.objects.get_or_create(name=NOMBRE_DIRECTORA)
    directora.permissions.set(Permission.objects.all())

    secretaria, _ = Group.objects.get_or_create(name=NOMBRE_SECRETARIA)
    secretaria.permissions.set(_permisos_secretaria())
