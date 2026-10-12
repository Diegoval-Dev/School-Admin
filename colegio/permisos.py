from functools import wraps

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied

from colegio.grupos import NOMBRE_DIRECTORA


def es_directora(usuario) -> bool:
    return usuario.is_superuser or usuario.groups.filter(name=NOMBRE_DIRECTORA).exists()


def solo_directora(vista):
    @staff_member_required
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        if not es_directora(request.user):
            raise PermissionDenied
        return vista(request, *args, **kwargs)

    return envoltura
