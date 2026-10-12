from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase

from colegio.grupos import NOMBRE_DIRECTORA, NOMBRE_SECRETARIA
from colegio.models import Docente, Estudiante, Genero
from colegio.services.codigos import siguiente_codigo_docente, siguiente_codigo_estudiante


class CodigosTests(TestCase):
    def test_codigo_estudiante_inicia_en_0001(self):
        self.assertEqual(siguiente_codigo_estudiante(2026), "2026-0001")

    def test_codigos_estudiante_correlativos_sin_colisiones(self):
        for _ in range(3):
            Estudiante.objects.create(primer_apellido="A", primer_nombre="B", genero=Genero.MASCULINO)

        codigos = list(Estudiante.objects.order_by("codigo").values_list("codigo", flat=True))

        self.assertEqual(len(codigos), len(set(codigos)))
        self.assertIn(f"{codigos[0][:5]}0003", codigos)

    def test_codigo_manual_no_se_repite_en_la_secuencia(self):
        Estudiante.objects.create(
            codigo="2026-0005", primer_apellido="A", primer_nombre="B", genero=Genero.MASCULINO
        )

        self.assertEqual(siguiente_codigo_estudiante(2026), "2026-0006")

    def test_codigo_docente_en_formato_d_nnn(self):
        Docente.objects.create(primer_apellido="C", primer_nombre="D", genero=Genero.FEMENINO)
        Docente.objects.create(primer_apellido="E", primer_nombre="F", genero=Genero.FEMENINO)

        codigos = sorted(Docente.objects.values_list("codigo", flat=True))

        self.assertEqual(codigos, ["D-001", "D-002"])
        self.assertEqual(siguiente_codigo_docente(), "D-003")


class PermisosTests(TestCase):
    def setUp(self):
        self.directora = Group.objects.get(name=NOMBRE_DIRECTORA)
        self.secretaria = Group.objects.get(name=NOMBRE_SECRETARIA)

    def permisos(self, grupo):
        return set(grupo.permissions.values_list("codename", flat=True))

    def test_directora_tiene_todos_los_permisos(self):
        self.assertEqual(self.directora.permissions.count(), Permission.objects.count())

    def test_secretaria_no_puede_borrar_ni_gestionar_usuarios(self):
        permisos = self.permisos(self.secretaria)

        self.assertFalse(any(codename.startswith("delete_") for codename in permisos))
        self.assertNotIn("add_user", permisos)
        self.assertIn("add_estudiante", permisos)
        self.assertIn("change_pago", permisos)


class ConfiguracionInicialTests(TestCase):
    def test_crea_directora_con_rol_y_acceso_de_staff(self):
        from django.test import Client

        cliente = Client()
        respuesta = cliente.post(
            "/configuracion-inicial/",
            {"username": "directora", "password1": "clave-muy-segura-2026", "password2": "clave-muy-segura-2026"},
        )

        usuario = get_user_model().objects.get(username="directora")
        self.assertRedirects(respuesta, "/login/", fetch_redirect_response=False)
        self.assertTrue(usuario.is_staff)
        self.assertTrue(usuario.groups.filter(name=NOMBRE_DIRECTORA).exists())

    def test_con_usuarios_la_configuracion_ya_no_esta_disponible(self):
        from django.test import Client

        get_user_model().objects.create_user("directora", password="clave-muy-segura-2026")

        respuesta = Client().get("/configuracion-inicial/")

        self.assertRedirects(respuesta, "/login/", fetch_redirect_response=False)

    def test_contrasena_corta_se_rechaza(self):
        from django.test import Client

        respuesta = Client().post(
            "/configuracion-inicial/",
            {"username": "directora", "password1": "corta", "password2": "corta"},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertFalse(get_user_model().objects.exists())
