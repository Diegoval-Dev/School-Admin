from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Font

from colegio.models import Concepto

FILA_ENCABEZADO = 1
FUENTE_ENCABEZADO = Font(bold=True)
ENCABEZADOS_PERSONA = ["No.", "Apellidos", "Nombres"]


def _libro_a_bytes(libro: Workbook) -> bytes:
    salida = BytesIO()
    libro.save(salida)
    return salida.getvalue()


def _hoja_con_encabezados(titulo: str, encabezados: list) -> tuple[Workbook, object]:
    libro = Workbook()
    hoja = libro.active
    hoja.title = titulo
    hoja.append(encabezados)
    for celda in hoja[FILA_ENCABEZADO]:
        celda.font = FUENTE_ENCABEZADO
    return libro, hoja


def libro_pagos(filas: list[dict]) -> bytes:
    encabezados = ENCABEZADOS_PERSONA + [concepto.label for concepto in Concepto]
    libro, hoja = _hoja_con_encabezados("Pagos", encabezados)
    for numero, fila in enumerate(filas, start=1):
        hoja.append(_valores_de_pagos(numero, fila))
    return _libro_a_bytes(libro)


def _valores_de_pagos(numero: int, fila: dict) -> list:
    estudiante = fila["matricula"].estudiante
    montos = [pago.monto if pago else None for _, pago in fila["celdas"]]
    return [numero, estudiante.apellidos, estudiante.nombres, *montos]


def libro_asistencia(filas: list[dict], dias: list) -> bytes:
    encabezados = ENCABEZADOS_PERSONA + [dia.day for dia in dias] + ["Presentes", "Ausentes", "Excusas"]
    libro, hoja = _hoja_con_encabezados("Asistencia", encabezados)
    for numero, fila in enumerate(filas, start=1):
        hoja.append(_valores_de_asistencia(numero, fila))
    return _libro_a_bytes(libro)


def _valores_de_asistencia(numero: int, fila: dict) -> list:
    estudiante = fila["matricula"].estudiante
    estados = [estado or "" for _, estado, _ in fila["celdas"]]
    totales = [fila["presentes"], fila["ausentes"], fila["excusas"]]
    return [numero, estudiante.apellidos, estudiante.nombres, *estados, *totales]


def libro_calificaciones(filas: list[dict], unidades: int) -> bytes:
    encabezados = ENCABEZADOS_PERSONA + [f"Unidad {unidad}" for unidad in range(1, unidades + 1)] + ["TOTAL", "PROMEDIO"]
    libro, hoja = _hoja_con_encabezados("Calificaciones", encabezados)
    for numero, fila in enumerate(filas, start=1):
        hoja.append(_valores_de_calificaciones(numero, fila))
    return _libro_a_bytes(libro)


def _valores_de_calificaciones(numero: int, fila: dict) -> list:
    estudiante = fila["matricula"].estudiante
    punteos = [punteo for _, punteo in fila["unidades"]]
    return [numero, estudiante.apellidos, estudiante.nombres, *punteos, fila["total"], fila["promedio"]]
