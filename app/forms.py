from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Perfil, Veterinario, Cliente

# ----------------------------------------------------------------------
# 🔹 FORMULARIO DE REGISTRO PRINCIPAL (PASO 1)
# ----------------------------------------------------------------------
class RegistroForm(UserCreationForm):
    # Campos adicionales que extienden al modelo User
    tipo = forms.ChoiceField(
        choices=[
            ('ADMINISTRADOR', 'Administrador'),
            ('VETERINARIO', 'Veterinario'),
            ('RECEPCIONISTA', 'Recepcionista'),
            ('CLIENTE', 'Cliente'),
        ],
        widget=forms.Select(attrs={"class": "form-select"}),
        label="Tipo de usuario"
    )

    rut = forms.CharField(
        max_length=12,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="RUT / DNI"
    )

    telefono = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={"class": "form-control"}),
        label="Teléfono"
    )

    class Meta:
        model = User
        # Campos base del modelo User + los personalizados del perfil
        fields = ["username", "email", "password1", "password2", "tipo", "rut", "telefono"]

        # Estilos Bootstrap para cada campo
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: juanperez"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def clean_username(self):
        """Evita nombres de usuario duplicados"""
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        """Evita correos duplicados"""
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email
        

# ----------------------------------------------------------------------
# 🔹 FORMULARIO DE VETERINARIO (PASO 2)
# ----------------------------------------------------------------------
class VeterinarioForm(forms.ModelForm):
    class Meta:
        model = Veterinario
        fields = ["nombre", "apellido", "especialidad", "licencia_profesional", "telefono_laboral"]
        labels = {
            "nombre": "Nombre",
            "apellido": "Apellido",
            "especialidad": "Especialidad",
            "licencia_profesional": "Licencia profesional",
            "telefono_laboral": "Teléfono laboral (opcional)",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "especialidad": forms.TextInput(attrs={"class": "form-control"}),
            "licencia_profesional": forms.TextInput(attrs={"class": "form-control"}),
            "telefono_laboral": forms.TextInput(attrs={"class": "form-control"}),
        }


# ----------------------------------------------------------------------
# 🔹 FORMULARIO DE CLIENTE (PASO 2)
# ----------------------------------------------------------------------
class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "apellido", "direccion"]
        labels = {
            "nombre": "Nombre",
            "apellido": "Apellido",
            "direccion": "Dirección",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
        }

