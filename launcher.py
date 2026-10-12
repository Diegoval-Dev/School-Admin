"""Punto de entrada del ejecutable: instancia única, respaldos, migraciones y servidor local."""
import logging
import os
import sys
import threading
import time
import webbrowser
from logging.handlers import RotatingFileHandler
from pathlib import Path

DJANGO_SETTINGS = "config.settings"
TITULO = "Sistema del Colegio"
NOMBRE_BASE_DATOS = "colegio.db"
NOMBRE_ARCHIVO_PUERTO = "puerto.txt"
CARPETA_REGISTROS = "logs"
NOMBRE_REGISTRO = "sistema.log"
TAMANIO_MAXIMO_REGISTRO = 1_000_000
REGISTROS_CONSERVADOS = 3
DIRECCION_LOOPBACK = "127.0.0.1"
THREADS_SERVIDOR = 4
RESPALDO_CADA_SEGUNDOS = 2 * 60 * 60
RETRASO_NAVEGADOR_SEGUNDOS = 1.0
FLAG_RESTAURAR = "--restaurar"
VARIABLE_SIN_NAVEGADOR = "COLEGIO_NO_NAVEGADOR"
MB_ICONERROR = 0x10
MB_ICONQUESTION = 0x20
MB_YESNO = 0x04
IDYES = 6
MENSAJE_ERROR_INESPERADO = "Ocurrió un error inesperado.\n\n{tipo}"
MENSAJE_MIGRACION_FALLIDA = (
    "No se pudo actualizar la base de datos. Se restauró la copia anterior; "
    "tus datos están a salvo. Contacta a soporte."
)
MENSAJE_BD_DANADA = (
    "La base de datos tiene un problema.\n\n"
    "¿Restaurar el respaldo bueno más reciente ({fecha})?"
)
MENSAJE_SIN_RESPALDO_BUENO = "La base de datos tiene un problema y no hay un respaldo bueno. Contacta a soporte."
MENSAJE_CONFIRMACION_RESTAURAR = "Se perderán los cambios hechos después de este respaldo. ¿Continuar?"
MENSAJE_RESTAURADO = "El respaldo se restauró correctamente."

logger = logging.getLogger("colegio.launcher")


def _configurar_registro(data_dir: Path) -> None:
    carpeta = data_dir / CARPETA_REGISTROS
    carpeta.mkdir(parents=True, exist_ok=True)
    manejador = RotatingFileHandler(
        carpeta / NOMBRE_REGISTRO, maxBytes=TAMANIO_MAXIMO_REGISTRO, backupCount=REGISTROS_CONSERVADOS, encoding="utf-8"
    )
    manejador.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(manejador)
    logger.setLevel(logging.INFO)


def _mensaje(texto: str, estilo: int = MB_ICONERROR) -> int:
    try:
        import ctypes

        return ctypes.windll.user32.MessageBoxW(0, texto, TITULO, estilo)
    except (AttributeError, OSError):
        print(f"{TITULO}: {texto}", file=sys.stderr)
        return 0


def _pregunta(texto: str) -> bool:
    return _mensaje(texto, MB_ICONQUESTION | MB_YESNO) == IDYES


def _configurar_django() -> None:
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", DJANGO_SETTINGS)
    import django

    django.setup()


def _abrir_instancia_existente(data_dir: Path) -> None:
    archivo = data_dir / NOMBRE_ARCHIVO_PUERTO
    puerto = archivo.read_text(encoding="utf-8").strip() if archivo.exists() else "8000"
    webbrowser.open(f"http://{DIRECCION_LOOPBACK}:{puerto}/")


def _abrir_navegador_despues(url: str) -> None:
    if os.environ.get(VARIABLE_SIN_NAVEGADOR) == "1":
        return
    threading.Timer(RETRASO_NAVEGADOR_SEGUNDOS, webbrowser.open, args=(url,)).start()


def _base_sana_o_recuperada(db: Path, backup_dir: Path) -> bool:
    from colegio.services.respaldos import archivo_sano

    if not db.exists() or archivo_sano(db):
        return True
    logger.error("La base de datos no pasó la verificación de integridad.")
    return _recuperar_ultimo_respaldo_bueno(db, backup_dir)


def _recuperar_ultimo_respaldo_bueno(db: Path, backup_dir: Path) -> bool:
    from colegio.services.respaldos import archivo_sano, listar_respaldos, restaurar

    buenos = [respaldo for respaldo in listar_respaldos(backup_dir) if archivo_sano(respaldo.ruta)]
    if not buenos:
        _mensaje(MENSAJE_SIN_RESPALDO_BUENO)
        return False
    fecha = f"{buenos[0].fecha:%d/%m/%Y %H:%M}"
    if not _pregunta(MENSAJE_BD_DANADA.format(fecha=fecha)):
        return False
    restaurar(db, buenos[0].ruta, backup_dir)
    logger.info("Base restaurada automáticamente desde un respaldo bueno.")
    return True


def _preparar_base(db: Path, backup_dir: Path) -> None:
    from colegio.services.migraciones import hay_migraciones_pendientes
    from colegio.services.respaldos import migrar_con_respaldo, respaldar_completo

    if not db.exists():
        _ejecutar_migraciones()
        return
    respaldar_completo(db, backup_dir)
    if not hay_migraciones_pendientes():
        return
    try:
        migrar_con_respaldo(db, backup_dir, _ejecutar_migraciones)
    except Exception:
        _mensaje(MENSAJE_MIGRACION_FALLIDA)
        raise


def _ejecutar_migraciones() -> None:
    from django.core.management import call_command

    call_command("migrate", interactive=False, verbosity=0)


def _iniciar_respaldo_periodico(db: Path, backup_dir: Path) -> None:
    threading.Thread(target=_bucle_respaldo, args=(db, backup_dir), daemon=True).start()


def _bucle_respaldo(db: Path, backup_dir: Path) -> None:
    from colegio.services.respaldos import respaldar_si_hubo_cambios

    while True:
        time.sleep(RESPALDO_CADA_SEGUNDOS)
        try:
            respaldar_si_hubo_cambios(db, backup_dir)
        except Exception as error:
            logger.error("Respaldo periódico fallido: %s", type(error).__name__)


def _servir(puerto: int, db: Path, backup_dir: Path) -> int:
    from waitress.server import create_server

    from colegio.services.respaldos import respaldar_completo
    from colegio.services.sistema import registrar_servidor
    from config.wsgi import application

    servidor = create_server(application, host=DIRECCION_LOOPBACK, port=puerto, threads=THREADS_SERVIDOR)
    registrar_servidor(servidor)
    _abrir_navegador_despues(f"http://{DIRECCION_LOOPBACK}:{puerto}/")
    servidor.run()
    if db.exists():
        respaldar_completo(db, backup_dir, etiqueta="cierre")
    logger.info("Sistema cerrado.")
    return 0


def _restaurar_con_dialogo(db: Path, backup_dir: Path) -> int:
    from tkinter import Tk, filedialog, messagebox

    from colegio.services.respaldos import RespaldoInvalido, restaurar

    raiz = Tk()
    raiz.withdraw()
    origen = filedialog.askopenfilename(
        title="Elige el respaldo a restaurar",
        initialdir=str(backup_dir),
        filetypes=[("Respaldo de base de datos", "*.db")],
    )
    if not origen:
        return 0
    if not (messagebox.askyesno(TITULO, MENSAJE_CONFIRMACION_RESTAURAR) and messagebox.askyesno(TITULO, "¿Seguro?")):
        return 0
    try:
        restaurar(db, Path(origen), backup_dir)
    except RespaldoInvalido:
        messagebox.showerror(TITULO, MENSAJE_SIN_RESPALDO_BUENO)
        return 1
    messagebox.showinfo(TITULO, MENSAJE_RESTAURADO)
    return 0


def _ejecutar(data_dir: Path, backup_dir: Path, db: Path) -> int:
    from colegio.services.instancia import puerto_libre

    _configurar_django()
    if FLAG_RESTAURAR in sys.argv:
        return _restaurar_con_dialogo(db, backup_dir)
    if not _base_sana_o_recuperada(db, backup_dir):
        return 1
    _preparar_base(db, backup_dir)
    puerto = puerto_libre()
    (data_dir / NOMBRE_ARCHIVO_PUERTO).write_text(str(puerto), encoding="utf-8")
    _iniciar_respaldo_periodico(db, backup_dir)
    return _servir(puerto, db, backup_dir)


def main() -> int:
    from colegio.services.instancia import adquirir_bloqueo
    from config.paths import get_backup_dir, get_data_dir

    data_dir = get_data_dir()
    backup_dir = get_backup_dir()
    db = data_dir / NOMBRE_BASE_DATOS
    _configurar_registro(data_dir)
    bloqueo = adquirir_bloqueo()
    if bloqueo is None:
        _abrir_instancia_existente(data_dir)
        return 0
    try:
        return _ejecutar(data_dir, backup_dir, db)
    except Exception as error:
        logger.error("Error al iniciar: %s", type(error).__name__)
        _mensaje(MENSAJE_ERROR_INESPERADO.format(tipo=type(error).__name__))
        return 1
    finally:
        bloqueo.close()


if __name__ == "__main__":
    sys.exit(main())
