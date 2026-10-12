from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

from colegio.grupos import NOMBRE_DIRECTORA


def hay_usuarios() -> bool:
    return get_user_model().objects.exists()


def asignar_rol_directora(usuario) -> None:
    usuario.is_staff = True
    usuario.save(update_fields=["is_staff"])
    grupo, _ = Group.objects.get_or_create(name=NOMBRE_DIRECTORA)
    usuario.groups.add(grupo)
