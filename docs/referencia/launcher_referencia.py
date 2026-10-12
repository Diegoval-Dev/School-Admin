"""
REFERENCIA de launcher.py (punto de entrada del .exe).  NO ejecutado todavía:
Claude Code debe completarlo, probarlo en desarrollo y luego congelado con PyInstaller.

Secuencia: instancia única -> rutas -> (--restaurar) -> integridad -> respaldo -> migrar
           -> puerto libre -> waitress en 127.0.0.1 -> abrir navegador -> respaldo periódico.
"""
import os
import socket
import sqlite3
import sys
import threading
import time
import webbrowser
from pathlib import Path

LOCK_PORT = 47653                      # puerto solo para bloqueo de instancia única
PUERTOS = range(8000, 8011)
RESPALDO_CADA_SEGUNDOS = 2 * 60 * 60   # 2 horas


# ───────────── Rutas (ver docs/EMPAQUETADO.md §2; mover a config/paths.py) ─────────────
def is_frozen() -> bool:
    return getattr(sys, "frozen", False)


def get_app_dir() -> Path:
    return Path(sys.executable).parent if is_frozen() else Path(__file__).resolve().parent


def get_root_dir() -> Path:
    """Carpeta raíz de datos. FUERA de la carpeta de la app."""
    env = os.environ.get("COLEGIO_ROOT")
    if env:
        return Path(env)
    return Path(r"C:\ColegioJGC") if is_frozen() else get_app_dir()


def get_data_dir() -> Path:
    p = Path(os.environ.get("COLEGIO_DATA_DIR", get_root_dir() / "datos"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def get_backup_dir() -> Path:
    p = get_root_dir() / "respaldos"
    p.mkdir(parents=True, exist_ok=True)
    return p


# ───────────── Mensajes al usuario (sin consola) ─────────────
def mostrar_error(titulo: str, mensaje: str) -> None:
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, mensaje, titulo, 0x10)  # MB_ICONERROR
    except Exception:
        print(f"{titulo}: {mensaje}", file=sys.stderr)


# ───────────── Instancia única ─────────────
def adquirir_bloqueo():
    """Devuelve el socket de bloqueo (mantenerlo vivo) o None si ya hay otra instancia."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", LOCK_PORT))
        s.listen(1)
        return s
    except OSError:
        s.close()
        return None


def abrir_instancia_existente(data_dir: Path) -> None:
    f = data_dir / "puerto.txt"
    puerto = f.read_text().strip() if f.exists() else "8000"
    webbrowser.open(f"http://127.0.0.1:{puerto}/")


def puerto_libre() -> int:
    for p in PUERTOS:
        with socket.socket() as s:
            if s.connect_ex(("127.0.0.1", p)) != 0:   # nadie escuchando → libre
                return p
    raise RuntimeError("No hay puertos libres entre 8000 y 8010.")


# ───────────── Integridad ─────────────
def integridad_ok(db: Path) -> bool:
    if not db.exists():
        return True  # primera vez: aún no hay base
    try:
        con = sqlite3.connect(db)
        try:
            return con.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        finally:
            con.close()
    except sqlite3.DatabaseError:
        return False


# ───────────── Principal ─────────────
def main() -> int:
    data_dir = get_data_dir()
    backup_dir = get_backup_dir()
    db = data_dir / "colegio.db"

    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    os.environ["COLEGIO_DATA_DIR"] = str(data_dir)

    lock = adquirir_bloqueo()
    if lock is None:
        abrir_instancia_existente(data_dir)
        return 0

    try:
        import django
        django.setup()
        from django.core.management import call_command
        from colegio.services import respaldos   # a implementar en Fase 5

        if "--restaurar" in sys.argv:
            return respaldos.flujo_restaurar_interactivo(db, backup_dir)

        if not integridad_ok(db):
            return respaldos.pantalla_rescate(db, backup_dir)   # ofrece restaurar el último bueno

        if db.exists():
            previo = respaldos.respaldar(db, backup_dir, etiqueta="inicio")

        try:
            call_command("migrate", interactive=False, verbosity=0)
        except Exception:
            if db.exists():
                respaldos.restaurar(db, previo, backup_dir)
            mostrar_error(
                "Sistema del Colegio",
                "No se pudo actualizar la base de datos. Se restauró la copia anterior; "
                "tus datos están a salvo. Contacta a soporte.",
            )
            raise

        puerto = puerto_libre()
        (data_dir / "puerto.txt").write_text(str(puerto))

        # Respaldo periódico en segundo plano
        def bucle_respaldo():
            while True:
                time.sleep(RESPALDO_CADA_SEGUNDOS)
                try:
                    respaldos.respaldar_si_hubo_cambios(db, backup_dir)
                except Exception:
                    pass   # registrar en datos/logs, sin datos personales

        threading.Thread(target=bucle_respaldo, daemon=True).start()

        # Servidor
        from waitress.server import create_server
        from config.wsgi import application
        servidor = create_server(application, host="127.0.0.1", port=puerto, threads=4)
        respaldos.registrar_servidor(servidor)   # lo usa el endpoint /sistema/cerrar/

        threading.Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{puerto}/")).start()
        servidor.run()                           # bloquea hasta servidor.close()

        # Cierre limpio: respaldo final
        if db.exists():
            respaldos.respaldar(db, backup_dir, etiqueta="cierre")
        return 0

    except Exception as e:  # último recurso: nunca una ventana en blanco
        mostrar_error("Sistema del Colegio", f"Ocurrió un error inesperado.\n\n{type(e).__name__}")
        return 1
    finally:
        lock.close()


if __name__ == "__main__":
    sys.exit(main())
