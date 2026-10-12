from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from colegio.models import CicloEscolar, Estudiante, Genero, Grado, Materia, Matricula, Nota
from colegio.services.notas import filas_de_notas, guardar_punteos


class NotasTestCase(TestCase):
    def setUp(self):
        self.ciclo = CicloEscolar.objects.create(anio=2026, activo=True)
        self.materia = Materia.objects.create(codigo="MAT-1B", nombre="Matemática", grado=Grado.PRIMERO)
        self.matricula = self._crear_matricula("Pérez", "Ana")
        self.usuario = get_user_model().objects.create_superuser("directora", "", "clave-muy-segura-2026")
        self.client.force_login(self.usuario)

    def _crear_matricula(self, apellido, nombre):
        estudiante = Estudiante.objects.create(primer_apellido=apellido, primer_nombre=nombre, genero=Genero.FEMENINO)
        return Matricula.objects.create(estudiante=estudiante, ciclo=self.ciclo, grado=Grado.PRIMERO)

    def fila(self):
        return filas_de_notas(self.ciclo, Grado.PRIMERO, self.materia)[0]


class GuardarNotasTests(NotasTestCase):
    def test_guardar_no_duplica_nota_de_la_misma_unidad(self):
        guardar_punteos(self.materia, {(self.matricula.pk, 1): "70"})
        guardar_punteos(self.materia, {(self.matricula.pk, 1): "85.5"})

        self.assertEqual(Nota.objects.count(), 1)
        self.assertEqual(Nota.objects.get().punteo, Decimal("85.50"))

    def test_punteo_fuera_de_rango_no_guarda_nada(self):
        otra = self._crear_matricula("Lara", "Luis")

        with self.assertRaises(ValidationError):
            guardar_punteos(
                self.materia,
                {(self.matricula.pk, 1): "70", (otra.pk, 1): "150"},
            )

        self.assertEqual(Nota.objects.count(), 0)

    def test_celda_vacia_se_ignora(self):
        guardar_punteos(self.materia, {(self.matricula.pk, 1): "  "})

        self.assertEqual(Nota.objects.count(), 0)

    def test_punteo_no_numerico_se_rechaza(self):
        for valor in ("abc", "NaN"):
            with self.subTest(valor=valor), self.assertRaises(ValidationError):
                guardar_punteos(self.materia, {(self.matricula.pk, 1): valor})


class PromedioTests(NotasTestCase):
    def test_total_y_promedio_solo_de_unidades_capturadas(self):
        guardar_punteos(self.materia, {(self.matricula.pk, 1): "70", (self.matricula.pk, 2): "80"})

        fila = self.fila()

        self.assertEqual(fila["total"], Decimal("150"))
        self.assertEqual(fila["promedio"], Decimal("75.00"))

    def test_sin_notas_no_hay_total_ni_promedio(self):
        fila = self.fila()

        self.assertIsNone(fila["total"])
        self.assertIsNone(fila["promedio"])


class VistasNotasTests(NotasTestCase):
    def test_tabla_responde(self):
        respuesta = self.client.get("/notas/", {"ciclo": self.ciclo.pk, "grado": Grado.PRIMERO, "materia": self.materia.pk})

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Pérez")

    def test_guardar_por_post_registra_punteos(self):
        respuesta = self.client.post(
            f"/notas/guardar/?ciclo={self.ciclo.pk}&grado={Grado.PRIMERO}&materia={self.materia.pk}",
            {f"punteo_{self.matricula.pk}_1": "90"},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Nota.objects.get().punteo, Decimal("90"))

    def test_excel_y_reporte_responden(self):
        query = f"ciclo={self.ciclo.pk}&grado={Grado.PRIMERO}&materia={self.materia.pk}"

        excel = self.client.get(f"/notas/excel/?{query}")
        reporte = self.client.get(f"/notas/reporte/?{query}")

        self.assertTrue(excel.content.startswith(b"PK"))
        self.assertEqual(reporte.status_code, 200)
        self.assertContains(reporte, "Calificaciones")
