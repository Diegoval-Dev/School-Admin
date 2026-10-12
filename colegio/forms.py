from django.contrib.auth.forms import UserCreationForm


class CuentaDirectoraForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        fields = ("username",)
