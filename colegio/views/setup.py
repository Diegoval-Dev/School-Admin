from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render

from colegio.forms import CuentaDirectoraForm
from colegio.services.usuarios import asignar_rol_directora, hay_usuarios

PLANTILLA = "colegio/configuracion_inicial.html"


def configuracion_inicial(request):
    if hay_usuarios():
        return redirect("admin:login")
    if request.method == "POST":
        form = CuentaDirectoraForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            asignar_rol_directora(usuario)
            return redirect("admin:login")
    else:
        form = CuentaDirectoraForm()
    return render(request, PLANTILLA, {"form": form})
