from django.apps import AppConfig
from django.db.models.signals import post_migrate


def _crear_grupos_al_migrar(sender, **kwargs):
    from colegio.grupos import crear_grupos_por_defecto

    crear_grupos_por_defecto()


class ColegioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "colegio"
    verbose_name = "Colegio"

    def ready(self):
        post_migrate.connect(_crear_grupos_al_migrar, sender=self, dispatch_uid="colegio_crear_grupos")
