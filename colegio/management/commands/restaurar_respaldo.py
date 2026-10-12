from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from colegio.services.respaldos import listar_respaldos, restaurar
from config.paths import get_backup_dir

CONFIRMACION = "RESTAURAR"


class Command(BaseCommand):
    help = "Restaura la base de datos desde un respaldo. Ejecutar con el sistema cerrado."

    def add_arguments(self, parser):
        parser.add_argument("--archivo", type=Path, help="Respaldo .db a restaurar (por ejemplo, copiado de la USB).")

    def handle(self, *args, **options):
        db = Path(settings.DATABASES["default"]["NAME"])
        origen = options["archivo"] or self._elegir_respaldo()
        self._confirmar(origen)
        restaurar(db, origen, get_backup_dir())
        self.stdout.write(self.style.SUCCESS(f"Base restaurada desde {origen.name}."))

    def _elegir_respaldo(self) -> Path:
        respaldos = listar_respaldos(get_backup_dir())
        if not respaldos:
            raise CommandError("No hay respaldos disponibles.")
        for numero, respaldo in enumerate(respaldos, start=1):
            self.stdout.write(f"{numero}. {respaldo.fecha:%d/%m/%Y %H:%M} · {respaldo.etiqueta}")
        eleccion = input("Número del respaldo a restaurar: ").strip()
        if not eleccion.isdigit() or not 1 <= int(eleccion) <= len(respaldos):
            raise CommandError("Opción inválida.")
        return respaldos[int(eleccion) - 1].ruta

    def _confirmar(self, origen: Path) -> None:
        self.stdout.write(f"Se perderán los cambios hechos después de {origen.name}.")
        if input(f"Escribe {CONFIRMACION} para continuar: ").strip() != CONFIRMACION:
            raise CommandError("Restauración cancelada.")
