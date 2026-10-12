import socket

LOCK_PORT = 47653
PUERTO_INICIAL = 8000
PUERTO_FINAL = 8010
DIRECCION_LOOPBACK = "127.0.0.1"


def adquirir_bloqueo(puerto: int = LOCK_PORT) -> socket.socket | None:
    """Devuelve el socket que mantiene el bloqueo, o None si otra instancia ya lo tiene."""
    bloqueo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        bloqueo.bind((DIRECCION_LOOPBACK, puerto))
        bloqueo.listen(1)
        return bloqueo
    except OSError:
        bloqueo.close()
        return None


def puerto_libre() -> int:
    for puerto in range(PUERTO_INICIAL, PUERTO_FINAL + 1):
        with socket.socket() as sonda:
            if sonda.connect_ex((DIRECCION_LOOPBACK, puerto)) != 0:
                return puerto
    raise RuntimeError(f"No hay puertos libres entre {PUERTO_INICIAL} y {PUERTO_FINAL}.")
