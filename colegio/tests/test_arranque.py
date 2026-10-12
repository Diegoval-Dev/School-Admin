from django.contrib.auth import get_user_model
from django.test import Client, TestCase


class ArranqueTests(TestCase):
    def test_sin_usuarios_redirige_a_configuracion_inicial(self):
        respuesta = Client().get("/login/")

        self.assertRedirects(respuesta, "/configuracion-inicial/", fetch_redirect_response=False)

    def test_login_responde_200_sin_recursos_externos(self):
        get_user_model().objects.create_user("directora", password="clave-segura-123")

        respuesta = Client().get("/login/")

        self.assertEqual(respuesta.status_code, 200)
        self.assertNotIn(b"https://", respuesta.content)
        self.assertNotIn(b"http://", respuesta.content.replace(b"http://www.w3.org/", b""))
