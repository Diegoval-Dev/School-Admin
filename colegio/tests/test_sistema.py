from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from colegio.services import sistema


class CerrarSistemaTests(TestCase):
    def setUp(self):
        self.usuario = get_user_model().objects.create_superuser("directora", "", "clave-muy-segura-2026")

    def test_cerrar_requiere_post(self):
        self.client.force_login(self.usuario)

        self.assertEqual(self.client.get("/sistema/cerrar/").status_code, 405)

    def test_cerrar_con_post_programa_el_cierre(self):
        self.client.force_login(self.usuario)

        with patch("colegio.views.sistema.cerrar_servidor_despues") as cerrar:
            respuesta = self.client.post("/sistema/cerrar/")

        self.assertEqual(respuesta.status_code, 200)
        cerrar.assert_called_once_with(1.0)

    def test_cerrar_sin_sesion_redirige_al_login(self):
        self.assertEqual(self.client.post("/sistema/cerrar/").status_code, 302)


class ServidorRegistradoTests(TestCase):
    def test_sin_servidor_registrado_no_hace_nada(self):
        sistema.registrar_servidor(None)

        sistema.cerrar_servidor_despues(1.0)
