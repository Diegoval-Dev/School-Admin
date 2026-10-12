from django.test import Client


def test_login_responde_200_sin_recursos_externos():
    respuesta = Client().get("/login/")

    assert respuesta.status_code == 200
    assert b"https://" not in respuesta.content
    assert b"http://" not in respuesta.content.replace(b"http://www.w3.org/", b"")
