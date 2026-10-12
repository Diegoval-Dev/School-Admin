from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font

from colegio.models import Concepto

TITULO_HOJA_PAGOS = "Pagos"
ENCABEZADOS_BASE = ["No.", "Apellidos", "Nombres"]
FILA_ENCABEZADO = 1
FUENTE_ENCABEZADO = Font(bold=True)


def libro_pagos(filas: list[dict]) -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.title = TITULO_HOJA_PAGOS
    encabezados = ENCABEZADOS_BASE + [concepto.label for concepto in Concepto]
    hoja.append(encabezados)
    for celda in hoja[FILA_ENCABEZADO]:
        celda.font = FUENTE_ENCABEZADO
    for numero, fila in enumerate(filas, start=1):
        hoja.append(_valores_de_fila(numero, fila))
    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _valores_de_fila(numero: int, fila: dict) -> list:
    estudiante = fila["matricula"].estudiante
    montos = [pago.monto if pago else None for _, pago in fila["celdas"]]
    return [numero, estudiante.apellidos, estudiante.nombres, *montos]
