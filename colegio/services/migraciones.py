from django.db import connection
from django.db.migrations.executor import MigrationExecutor


def hay_migraciones_pendientes() -> bool:
    ejecutor = MigrationExecutor(connection)
    return bool(ejecutor.migration_plan(ejecutor.loader.graph.leaf_nodes()))
