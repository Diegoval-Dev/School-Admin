from datetime import date
from decimal import Decimal
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError
from django.test import TestCase

from colegio.models import (
    CicloEscolar,
    Concepto,
    Estudiante,
    Genero,
    Grado,
    Materia,
    Matricula,
    Nota,
    Pago,
)


def crear_estudiante(**kwargs):
    datos = {
        "primer_apellido": "Pérez",
        "primer_nombre": "Ana",
        "genero": Genero.FEMENINO,
    }
    datos.update(kwargs)
    return Estudiante.objects.create(**datos)


class EdadTests(TestCase):
    def test_edad_no_cumplida_aun_resta_un_anio(self):
        estudiante = crear_estudiante(fecha_nacimiento=date(2016, 5, 11))

        with patch("colegio.models.timezone.localdate", return_value=date(2026, 5, 10)):
            self.assertEqual(estudiante.edad, 9)

    def test_edad_el_dia_del_cumpleanios(self):
        estudiante = crear_estudiante(fecha_nacimiento=date(2016, 5, 10))

        with patch("colegio.models.timezone.localdate", return_value=date(2026, 5, 10)):
            self.assertEqual(estudiante.edad, 10)

    def test_edad_sin_fecha_es_none(self):
        self.assertIsNone(crear_estudiante().edad)


class DocumentoTests(TestCase):
    def test_cui_con_13_digitos_se_normaliza_sin_espacios(self):
        estudiante = crear_estudiante(numero_documento="1234 56789 0123")

        estudiante.clean()

        self.assertEqual(estudiante.numero_documento, "1234567890123")

    def test_cui_invalido_se_rechaza(self):
        estudiante = crear_estudiante(numero_documento="123")

        with self.assertRaises(ValidationError) as contexto:
            estudiante.clean()

        self.assertIn("numero_documento", contexto.exception.message_dict)

    def test_pasaporte_no_exige_longitud(self):
        estudiante = crear_estudiante(tipo_documento="PAS", numero_documento="AB12")

        estudiante.clean()

        self.assertEqual(estudiante.numero_documento, "AB12")


class MatriculaTests(TestCase):
    def setUp(self):
        self.ciclo = CicloEscolar.objects.create(anio=2026, activo=True)
        self.estudiante = crear_estudiante()

    def test_un_estudiante_no_puede_tener_dos_matriculas_en_el_mismo_ciclo(self):
        Matricula.objects.create(estudiante=self.estudiante, ciclo=self.ciclo, grado=Grado.PRIMERO)

        with self.assertRaises(IntegrityError), transaction.atomic():
            Matricula.objects.create(estudiante=self.estudiante, ciclo=self.ciclo, grado=Grado.SEGUNDO)


class PagoTests(TestCase):
    def setUp(self):
        ciclo = CicloEscolar.objects.create(anio=2026)
        self.matricula = Matricula.objects.create(
            estudiante=Estudiante.objects.create(primer_apellido="Lopez", primer_nombre="Luis", genero=Genero.MASCULINO),
            ciclo=ciclo,
            grado=Grado.PRIMERO,
        )

    def registrar_pago(self, **kwargs):
        datos = {
            "matricula": self.matricula,
            "concepto": Concepto.ENERO,
            "monto": Decimal("150.00"),
            "fecha_pago": date(2026, 1, 15),
        }
        datos.update(kwargs)
        return Pago.objects.create(**datos)

    def test_no_se_duplica_pago_vigente_por_concepto(self):
        self.registrar_pago()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.registrar_pago()

    def test_anular_permite_volver_a_registrar_el_concepto(self):
        self.registrar_pago(anulado=True, motivo_anulacion="Recibo equivocado")

        self.registrar_pago()

        self.assertEqual(Pago.objects.filter(concepto=Concepto.ENERO).count(), 2)

    def test_anulado_exige_motivo(self):
        pago = Pago(matricula=self.matricula, concepto=Concepto.FEBRERO, monto=Decimal("10"),
                    fecha_pago=date(2026, 2, 1), anulado=True)

        with self.assertRaises(ValidationError):
            pago.clean()

    def test_no_se_puede_borrar_estudiante_con_pagos(self):
        self.registrar_pago()

        with self.assertRaises(ProtectedError):
            self.matricula.estudiante.delete()

    def test_totales_se_suman_con_decimal(self):
        self.registrar_pago(concepto=Concepto.ENERO, monto=Decimal("0.10"))
        self.registrar_pago(concepto=Concepto.FEBRERO, monto=Decimal("0.20"))

        total = sum(pago.monto for pago in Pago.objects.all())

        self.assertEqual(total, Decimal("0.30"))


class NotaTests(TestCase):
    def setUp(self):
        ciclo = CicloEscolar.objects.create(anio=2026)
        self.matricula = Matricula.objects.create(
            estudiante=crear_estudiante(), ciclo=ciclo, grado=Grado.PRIMERO
        )
        self.materia = Materia.objects.create(codigo="MAT-1B", nombre="Matemática", grado=Grado.PRIMERO)

    def nota(self, **kwargs):
        datos = {"matricula": self.matricula, "materia": self.materia, "unidad": 1, "punteo": Decimal("80")}
        datos.update(kwargs)
        return Nota(**datos)

    def test_unidad_fuera_de_rango_se_rechaza(self):
        with self.assertRaises(ValidationError):
            self.nota(unidad=5).clean()

    def test_punteo_fuera_de_rango_se_rechaza(self):
        with self.assertRaises(ValidationError):
            self.nota(punteo=Decimal("101")).clean()

    def test_materia_de_otro_grado_se_rechaza(self):
        otra = Materia.objects.create(codigo="MAT-2B", nombre="Ciencias", grado=Grado.SEGUNDO)

        with self.assertRaises(ValidationError):
            self.nota(materia=otra).clean()

    def test_una_nota_por_unidad_y_materia(self):
        self.nota().save()

        with self.assertRaises(IntegrityError), transaction.atomic():
            self.nota().save()
