import threading

_servidor_activo = None


def registrar_servidor(servidor) -> None:
    global _servidor_activo
    _servidor_activo = servidor


def cerrar_servidor_despues(retraso_segundos: float) -> None:
    if _servidor_activo is None:
        return
    threading.Timer(retraso_segundos, _servidor_activo.close).start()
