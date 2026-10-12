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


def _hojas_completas():
    from colegio.models import Asistencia, CicloEscolar, Estudiante, Docente, Materia, Matricula, Nota, Pago

    return [
        ("Estudiantes", Estudiante.objects.all(), [
            ("Código", lambda e: e.codigo), ("Apellidos", lambda e: e.apellidos),
            ("Nombres", lambda e: e.nombres), ("Fecha de nacimiento", lambda e: e.fecha_nacimiento),
            ("Género", lambda e: e.get_genero_display()), ("Documento", lambda e: e.numero_documento),
            ("Estado", lambda e: e.get_estado_display()), ("Observaciones", lambda e: e.observaciones),
        ]),
        ("Docentes", Docente.objects.all(), [
            ("Código", lambda d: d.codigo), ("Apellidos", lambda d: d.apellidos),
            ("Nombres", lambda d: d.nombres), ("Tipo", lambda d: d.get_tipo_display()),
            ("Teléfono 1", lambda d: d.telefono_1), ("Teléfono 2", lambda d: d.telefono_2),
            ("Activo", lambda d: "Sí" if d.activo else "No"),
        ]),
        ("Materias", Materia.objects.all(), [
            ("Código", lambda m: m.codigo), ("Nombre", lambda m: m.nombre), ("Grado", lambda m: m.get_grado_display()),
        ]),
        ("Ciclos", CicloEscolar.objects.all(), [
            ("Año", lambda c: c.anio), ("Actual", lambda c: "Sí" if c.activo else "No"),
        ]),
        ("Matrículas", Matricula.objects.select_related("estudiante", "ciclo"), [
            ("Estudiante", lambda m: str(m.estudiante)), ("Ciclo", lambda m: m.ciclo.anio),
            ("Grado", lambda m: m.get_grado_display()), ("Jornada", lambda m: m.get_jornada_display()),
            ("Activa", lambda m: "Sí" if m.activa else "No"),
        ]),
        ("Pagos", Pago.objects.select_related("matricula__estudiante"), [
            ("Estudiante", lambda p: str(p.matricula.estudiante)), ("Concepto", lambda p: p.get_concepto_display()),
            ("Monto", lambda p: p.monto), ("Fecha", lambda p: p.fecha_pago), ("No. recibo", lambda p: p.numero_recibo),
            ("Anulado", lambda p: "Sí" if p.anulado else "No"), ("Motivo anulación", lambda p: p.motivo_anulacion),
        ]),
        ("Asistencia", Asistencia.objects.select_related("matricula__estudiante"), [
            ("Estudiante", lambda a: str(a.matricula.estudiante)), ("Fecha", lambda a: a.fecha),
            ("Estado", lambda a: a.get_estado_display()),
        ]),
        ("Notas", Nota.objects.select_related("matricula__estudiante", "materia"), [
            ("Estudiante", lambda n: str(n.matricula.estudiante)), ("Materia", lambda n: n.materia.nombre),
            ("Unidad", lambda n: n.unidad), ("Punteo", lambda n: n.punteo),
        ]),
    ]


def libro_completo() -> bytes:
    libro = Workbook()
    libro.remove(libro.active)
    for titulo, registros, columnas in _hojas_completas():
        hoja = libro.create_sheet(titulo)
        hoja.append([encabezado for encabezado, _ in columnas])
        for celda in hoja[FILA_ENCABEZADO]:
            celda.font = FUENTE_ENCABEZADO
        for registro in registros:
            hoja.append([acceso(registro) for _, acceso in columnas])
    return _libro_a_bytes(libro)
