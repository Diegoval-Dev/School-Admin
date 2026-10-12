from datetime import date
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from colegio.models import CicloEscolar, Concepto, Estudiante, Genero, Grado, Jornada, Matricula, Pago
from colegio.services.pagos import (
    anular_pago,
    filas_de_pagos,
    matriculas_pendientes,
    registrar_pago,
    total_pagado,
)

DATOS_PAGO = {"monto": Decimal("150.00"), "fecha_pago": date(2026, 1, 15)}


class PagosTestCase(TestCase):
    def setUp(self):
        self.ciclo = CicloEscolar.objects.create(anio=2026, activo=True)
        self.matricula = self._crear_matricula("Pérez", "Ana")
        self.usuario = get_user_model().objects.create_superuser("directora", "", "clave-muy-segura-2026")
        self.client.force_login(self.usuario)

    def _crear_matricula(self, apellido, nombre, grado=Grado.PRIMERO):
        estudiante = Estudiante.objects.create(primer_apellido=apellido, primer_nombre=nombre, genero=Genero.FEMENINO)
        return Matricula.objects.create(estudiante=estudiante, ciclo=self.ciclo, grado=grado)


class ServicioPagosTests(PagosTestCase):
    def test_no_registra_pago_vigente_duplicado(self):
        registrar_pago(self.matricula, Concepto.ENERO, **DATOS_PAGO)

        with self.assertRaises(ValidationError):
            registrar_pago(self.matricula, Concepto.ENERO, **DATOS_PAGO)

    def test_tras_anular_se_puede_volver_a_registrar(self):
        pago = registrar_pago(self.matricula, Concepto.ENERO, **DATOS_PAGO)
        anular_pago(pago, "Recibo equivocado")

        registrar_pago(self.matricula, Concepto.ENERO, **DATOS_PAGO)

        self.assertEqual(Pago.objects.filter(concepto=Concepto.ENERO, anulado=True).count(), 1)

    def test_anular_sin_motivo_falla(self):
        pago = registrar_pago(self.matricula, Concepto.ENERO, **DATOS_PAGO)

        with self.assertRaises(ValidationError):
            anular_pago(pago, "   ")

        pago.refresh_from_db()
        self.assertFalse(pago.anulado)

    def test_total_pagado_ignora_anulados_y_usa_decimal(self):
        registrar_pago(self.matricula, Concepto.ENERO, monto=Decimal("0.10"), fecha_pago=date(2026, 1, 1))
        anulado = registrar_pago(self.matricula, Concepto.FEBRERO, monto=Decimal("99.00"), fecha_pago=date(2026, 2, 1))
        anular_pago(anulado, "Duplicado")
        registrar_pago(self.matricula, Concepto.MARZO, monto=Decimal("0.20"), fecha_pago=date(2026, 3, 1))

        self.assertEqual(total_pagado(self.matricula), Decimal("0.30"))

    def test_pendientes_excluye_a_quien_ya_pago(self):
        otra = self._crear_matricula("Lara", "Luis")
        registrar_pago(self.matricula, Concepto.ENERO, **DATOS_PAGO)

        pendientes = list(matriculas_pendientes(self.ciclo, Concepto.ENERO))

        self.assertEqual(pendientes, [otra])

    def test_filas_de_pagos_separan_vigentes_de_anulados(self):
        pago = registrar_pago(self.matricula, Concepto.ENERO, **DATOS_PAGO)
        anular_pago(pago, "Error")

        fila = filas_de_pagos(self.ciclo, Grado.PRIMERO, Jornada.DIARIO)[0]

        self.assertTrue(all(pago_celda is None for _, pago_celda in fila["celdas"]))


class VistasPagosTests(PagosTestCase):
    def test_tabla_responde_y_muestra_estudiante(self):
        respuesta = self.client.get("/pagos/", {"ciclo": self.ciclo.pk, "grado": Grado.PRIMERO, "jornada": Jornada.DIARIO})

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Pérez")

    def test_registrar_pago_por_post_guarda_y_redirige(self):
        respuesta = self.client.post(
            f"/pagos/registrar/{self.matricula.pk}/{Concepto.ENERO}/",
            {"monto": "150.00", "fecha_pago": "2026-01-15", "numero_recibo": "", "observaciones": ""},
        )

        self.assertEqual(respuesta.status_code, 302)
        self.assertTrue(Pago.objects.filter(matricula=self.matricula, concepto=Concepto.ENERO).exists())

    def test_concepto_invalido_responde_404(self):
        respuesta = self.client.get(f"/pagos/registrar/{self.matricula.pk}/99/")

        self.assertEqual(respuesta.status_code, 404)

    def test_anular_por_post_marca_el_pago(self):
        pago = registrar_pago(self.matricula, Concepto.ENERO, **DATOS_PAGO)

        self.client.post(f"/pagos/anular/{pago.pk}/", {"motivo": "Recibo equivocado"})

        pago.refresh_from_db()
        self.assertTrue(pago.anulado)
        self.assertEqual(pago.motivo_anulacion, "Recibo equivocado")

    def test_excel_se_descarga_como_xlsx(self):
        respuesta = self.client.get("/pagos/excel/", {"ciclo": self.ciclo.pk})

        self.assertEqual(
            respuesta["Content-Type"],
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        self.assertTrue(respuesta.content.startswith(b"PK"))

    def test_reporte_imprimible_responde(self):
        respuesta = self.client.get("/pagos/reporte/", {"ciclo": self.ciclo.pk})

        self.assertEqual(respuesta.status_code, 200)
        self.assertContains(respuesta, "Julio González Celis")

    def test_vistas_requieren_staff(self):
        self.client.logout()

        respuesta = self.client.get("/pagos/")

        self.assertEqual(respuesta.status_code, 302)
