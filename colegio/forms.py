from django import forms
from django.contrib.auth.forms import UserCreationForm

from colegio.models import Pago

MAX_LONGITUD_MOTIVO = 255


class CuentaDirectoraForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ("username",)


class PagoForm(forms.ModelForm):
    class Meta:
        model = Pago
        fields = ("monto", "fecha_pago", "numero_recibo", "observaciones")
        widgets = {"fecha_pago": forms.DateInput(attrs={"type": "date"})}


class AnulacionPagoForm(forms.Form):
    motivo = forms.CharField(label="Motivo de la anulación", max_length=MAX_LONGITUD_MOTIVO)
