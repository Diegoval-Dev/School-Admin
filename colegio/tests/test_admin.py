from django.contrib.auth import get_user_model
from django.test import TestCase

from colegio.admin import EstudianteAdmin
from colegio.models import Estudiante, Genero


class AdminTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_superuser("directora", "", "clave-muy-segura-2026")
        self.client.force_login(self.usuario)
        self.estudiante = Estudiante.objects.create(
            primer_apellido="Ramírez", primer_nombre="Sofía", genero=Genero.FEMENINO
        )

    def test_listado_de_estudiantes_carga(self):
        respuesta = self.client.get("/colegio/estudiante/")

        self.assertEqual(respuesta.status_code, 200)

    def test_pagina_de_historial_del_estudiante_carga(self):
        url = f"/colegio/estudiante/{self.estudiante.pk}/history/"

        respuesta = self.client.get(url)

        self.assertEqual(respuesta.status_code, 200)

    def test_no_se_puede_borrar_estudiante_desde_admin(self):
        self.assertFalse(EstudianteAdmin(Estudiante, None).has_delete_permission(None, self.estudiante))
