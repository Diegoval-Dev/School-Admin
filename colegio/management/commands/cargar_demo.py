from datetime import date, timedelta
from decimal import Decimal
from itertools import cycle

from django.core.management.base import BaseCommand
from django.db import transaction

from colegio.models import (
    Asignacion,
    Asistencia,
    CicloEscolar,
    Concepto,
    Contacto,
    Docente,
    EstadoAsistencia,
    Estudiante,
    Genero,
    Grado,
    Materia,
    Matricula,
    Pago,
    Relacion,
    Responsable,
)

ANIO_DEMO = 2026
TOTAL_ESTUDIANTES = 40
NOMBRES = ["Lucía", "Mateo", "Valeria", "Diego", "Camila", "Andrés", "Renata", "Hugo", "Paula", "Bruno"]
APELLIDOS = ["Morales", "Cifuentes", "Ajcalón", "Solórzano", "Velásquez", "Xitumul", "Barrios", "Monzón"]
MATERIAS_POR_GRADO = ["Matemática", "Comunicación", "Ciencias Naturales", "Estudios Sociales"]
JORNADAS = ("D", "FS")
CONCEPTOS_PAGADOS = [Concepto.INSCRIPCION, Concepto.ENERO, Concepto.FEBRERO, Concepto.MARZO]
MONTO_MENSUALIDAD = Decimal("150.00")
MONTO_INSCRIPCION = Decimal("250.00")
DIAS_ASISTENCIA = 10
ESTADOS_ASISTENCIA = [EstadoAsistencia.PRESENTE, EstadoAsistencia.PRESENTE, EstadoAsistencia.AUSENTE]


class Command(BaseCommand):
    help = "Carga datos ficticios para probar el sistema. Nunca usar con datos reales."

    @transaction.atomic
    def handle(self, *args, **options):
        ciclo = self._crear_ciclo()
        materias = self._crear_materias()
        self._crear_docentes(ciclo, materias)
        self._crear_estudiantes(ciclo)
        self.stdout.write(self.style.SUCCESS(f"Datos de demostración cargados para {ciclo}."))

    def _crear_ciclo(self):
        ciclo, _ = CicloEscolar.objects.update_or_create(anio=ANIO_DEMO, defaults={"activo": True})
        return ciclo

    def _crear_materias(self):
        materias = []
        for grado in Grado:
            for nombre in MATERIAS_POR_GRADO:
                codigo = f"MAT-{grado.value}-{nombre[:3].upper()}"
                materia, _ = Materia.objects.get_or_create(
                    codigo=codigo, defaults={"nombre": nombre, "grado": grado}
                )
                materias.append(materia)
        return materias

    def _crear_docentes(self, ciclo, materias):
        for indice in range(6):
            docente = Docente.objects.create(
                primer_apellido=APELLIDOS[indice],
                primer_nombre=NOMBRES[indice],
                genero=Genero.MASCULINO if indice % 2 else Genero.FEMENINO,
            )
            Asignacion.objects.create(docente=docente, materia=materias[indice], ciclo=ciclo)

    def _crear_estudiantes(self, ciclo):
        grados = cycle(Grado.values)
        for indice in range(TOTAL_ESTUDIANTES):
            grado = next(grados)
            estudiante = self._crear_estudiante(indice)
            matricula = Matricula.objects.create(
                estudiante=estudiante,
                ciclo=ciclo,
                grado=grado,
                jornada=JORNADAS[indice % len(JORNADAS)],
            )
            self._crear_responsable_y_contacto(estudiante, indice)
            self._crear_pagos(matricula)
            self._crear_asistencias(matricula)

    def _crear_estudiante(self, indice):
        return Estudiante.objects.create(
            primer_apellido=APELLIDOS[indice % len(APELLIDOS)],
            segundo_apellido=APELLIDOS[(indice + 3) % len(APELLIDOS)],
            primer_nombre=NOMBRES[indice % len(NOMBRES)],
            genero=Genero.MASCULINO if indice % 2 else Genero.FEMENINO,
            fecha_nacimiento=date(2017, 1, 1) + timedelta(days=indice * 17),
        )

    def _crear_responsable_y_contacto(self, estudiante, indice):
        Responsable.objects.create(
            estudiante=estudiante,
            relacion=Relacion.MADRE,
            nombre_completo=f"Madre ficticia {indice}",
        )
        Contacto.objects.create(
            estudiante=estudiante,
            telefono=f"5555-{indice:04d}",
            nombre_responsable=f"Madre ficticia {indice}",
        )

    def _crear_pagos(self, matricula):
        for concepto in CONCEPTOS_PAGADOS:
            monto = MONTO_INSCRIPCION if concepto == Concepto.INSCRIPCION else MONTO_MENSUALIDAD
            Pago.objects.create(
                matricula=matricula,
                concepto=concepto,
                monto=monto,
                fecha_pago=date(ANIO_DEMO, 1, 15),
            )

    def _crear_asistencias(self, matricula):
        estados = cycle(ESTADOS_ASISTENCIA)
        for dia in range(DIAS_ASISTENCIA):
            Asistencia.objects.create(
                matricula=matricula,
                fecha=date(ANIO_DEMO, 1, 5) + timedelta(days=dia),
                estado=next(estados),
            )
