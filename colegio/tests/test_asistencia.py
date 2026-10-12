from datetime import date

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from colegio.models import Asistencia, CicloEscolar, EstadoAsistencia, Estudiante, Genero, Grado, Jornada, Matricula
from colegio.services.asistencia import ciclar_asistencia, dias_del_mes, filas_de_asistencia


class AsistenciaTestCase(TestCase):
    def setUp(self):
        self.ciclo = CicloEscolar.objects.create(anio=2026, activo=True)
        self.matricula = self._crear_matricula("Pérez", "Ana")
        self.usuario = get_user_model().objects.create_superuser("directora", "", "clave-muy-segura-2026")
        self.client.force_login(self.usuario)

    def _crear_matricula(self, apellido, nombre, jornada=Jornada.DIARIO, activa=True):
        estudiante = Estudiante.objects.create(primer_apellido=apellido, primer_nombre=nombre, genero=Genero.FEMENINO)
        return Matricula.objects.create(
            estudiante=estudiante, ciclo=self.ciclo, grado=Grado.PRIMERO, jornada=jornada, activa=activa
        )


class DiasDelMesTests(TestCase):
    def test_diario_incluye_todos_los_dias_del_mes(self):
        self.assertEqual(len(dias_del_mes(2026, 2, Jornada.DIARIO)), 28)

    def test_fin_de_semana_solo_sabados_y_domingos(self):
        dias = dias_del_mes(2026, 1, Jornada.FIN_SEMANA)

        self.assertTrue(all(dia.weekday() >= 5 for dia in dias))
        self.assertEqual(len(dias), 9)


class CiclarAsistenciaTests(AsistenciaTestCase):
    def test_primer_clic_marca_presente(self):
        ciclar_asistencia(self.matricula, date(2026, 1, 5))

        self.assertEqual(Asistencia.objects.get().estado, EstadoAsistencia.PRESENTE)

    def test_clics_cambian_el_estado_en_orden_sin_borrar(self):
        dia = date(2026, 1, 5)
        ciclar_asistencia(self.matricula, dia)
        ciclar_asistencia(self.matricula, dia)
        ciclar_asistencia(self.matricula, dia)
        ciclar_asistencia(self.matricula, dia)

        estados = list(Asistencia.objects.values_list("estado", flat=True))
        self.assertEqual(estados, [EstadoAsistencia.PRESENTE])

    def test_una_asistencia_por_matricula_y_dia(self):
        dia = date(2026, 1, 5)
        ciclar_asistencia(self.matricula, dia)
        ciclar_asistencia(self.matricula, dia)

        self.assertEqual(Asistencia.objects.filter(matricula=self.matricula, fecha=dia).count(), 1)

    def test_matricula_inactiva_no_recibe_asistencia(self):
        inactiva = self._crear_matricula("Lara", "Luis", activa=False)

        with self.assertRaises(ValidationError):
            ciclar_asistencia(inactiva, date(2026, 1, 5))

    def test_filas_solo_incluyen_matriculas_activas_del_filtro(self):
        self._crear_matricula("Lara", "Luis", activa=False)
        self._crear_matricula("Gómez", "Eva", jornada=Jornada.FIN_SEMANA)
        activas = Matricula.objects.filter(activa=True, jornada=Jornada.DIARIO)

        filas = filas_de_asistencia(activas, dias_del_mes(2026, 1, Jornada.DIARIO))

        self.assertEqual([fila["matricula"] for fila in filas], [self.matricula])


class TotalesAsistenciaTests(AsistenciaTestCase):
    def test_totales_por_estudiante(self):
        ciclar_asistencia(self.matricula, date(2026, 1, 5))
        ciclar_asistencia(self.matricula, date(2026, 1, 6))
        ciclar_asistencia(self.matricula, date(2026, 1, 6))
        ciclar_asistencia(self.matricula, date(2026, 1, 7))
        ciclar_asistencia(self.matricula, date(2026, 1, 7))
        ciclar_asistencia(self.matricula, date(2026, 1, 7))

        fila = filas_de_asistencia(
            Matricula.objects.filter(pk=self.matricula.pk), dias_del_mes(2026, 1, Jornada.DIARIO)
        )[0]

        self.assertEqual((fila["presentes"], fila["ausentes"], fila["excusas"]), (1, 1, 1))


class VistasAsistenciaTests(AsistenciaTestCase):
    def test_tabla_responde_con_el_estudiante(self):
        respuesta = self.client.get("/asistencia/", {"ciclo": self.ciclo.pk, "mes": 1})

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Pérez")

    def test_clic_en_celda_cambia_estado_y_redirige(self):
        respuesta = self.client.post(
            "/asistencia/ciclar/", {"celda": f"{self.matricula.pk}|2026-01-05"}
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertEqual(Asistencia.objects.get().estado, EstadoAsistencia.PRESENTE)

    def test_celda_invalida_responde_404(self):
        respuesta = self.client.post("/asistencia/ciclar/", {"celda": "basura"})

        self.assertEqual(respuesta.status_code, 404)

    def test_excel_y_reporte_responden(self):
        excel = self.client.get("/asistencia/excel/", {"ciclo": self.ciclo.pk, "mes": 1})
        reporte = self.client.get("/asistencia/reporte/", {"ciclo": self.ciclo.pk, "mes": 1})

        self.assertTrue(excel.content.startswith(b"PK"))
        self.assertEqual(reporte.status_code, 200)
