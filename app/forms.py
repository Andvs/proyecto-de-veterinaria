from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Mascota, Cita, Consulta, Cliente, Veterinario, Recepcionista, Perfil


class RegistroForm(UserCreationForm):
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
    rut = forms.CharField(max_length=12, widget=forms.TextInput(attrs={"class": "form-control"}), label="RUT / DNI")
    telefono = forms.CharField(max_length=15, widget=forms.TextInput(attrs={"class": "form-control"}), label="Teléfono")

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2", "tipo", "rut", "telefono"]
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Ej: juanperez"}),
            "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control"}),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Este nombre de usuario ya está en uso.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email



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



class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nombre", "apellido", "direccion"]
        labels = {"nombre": "Nombre", "apellido": "Apellido", "direccion": "Dirección"}
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "direccion": forms.TextInput(attrs={"class": "form-control"}),
        }

class RegistroClienteRecepForm(UserCreationForm):
    
    rut = forms.CharField(label="RUT / DNI", max_length=12)
    telefono = forms.CharField(label="Teléfono", max_length=15)

    
    nombre = forms.CharField(label="Nombre", max_length=45)
    apellido = forms.CharField(label="Apellido", max_length=45)
    direccion = forms.CharField(label="Dirección", max_length=100, required=False)

    email = forms.EmailField(label="Email", required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password1", "password2",
                "rut", "telefono", "nombre", "apellido", "direccion"]

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        for name, field in self.fields.items():
            if not field.widget.attrs.get("class"):
                field.widget.attrs["class"] = "form-control"

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Ya existe un usuario con este email.")
        return email

    def clean_rut(self):
        rut = self.cleaned_data["rut"].strip()
        if Perfil.objects.filter(rut__iexact=rut).exists():
            raise forms.ValidationError("Ya existe un perfil con este RUT/DNI.")
        return rut


class MascotaForm(forms.ModelForm):
    class Meta:
        model = Mascota
        fields = ["dueno", "nombre", "especie", "raza", "fecha_nacimiento", "sexo", "color"]
        widgets = {
            "dueno": forms.Select(attrs={"class": "form-select"}),
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "especie": forms.Select(attrs={"class": "form-control"}),
            "raza": forms.TextInput(attrs={"class": "form-control"}),
            "fecha_nacimiento": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "sexo": forms.Select(attrs={"class": "form-select"}),
            "color": forms.TextInput(attrs={"class": "form-control"}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user and hasattr(user, 'perfil') and user.perfil.tipo == 'CLIENTE':
            self.fields.pop('dueno')



class RecepcionistaForm(forms.ModelForm):
    class Meta:
        model = Recepcionista
        fields = ["nombre", "apellido", "telefono"]
        labels = {
            "nombre": "Nombre",
            "apellido": "Apellido",
            "telefono": "Teléfono",
        }
        widgets = {
            "nombre": forms.TextInput(attrs={"class": "form-control"}),
            "apellido": forms.TextInput(attrs={"class": "form-control"}),
            "telefono": forms.TextInput(attrs={"class": "form-control"}),
        }


class CitaForm(forms.ModelForm):
    dueno = forms.ModelChoiceField(
        queryset=Cliente.objects.all(),
        label="Dueño",
        widget=forms.Select(attrs={"class": "form-select", "id": "id_dueno"}),
        required=True
    )
    
    class Meta:
        model = Cita
        fields = ["mascota", "veterinario", "fecha_hora", "motivo", "observaciones"]
        labels = {
            "mascota": "Mascota",
            "veterinario": "Veterinario",
            "fecha_hora": "Fecha y hora",
            "motivo": "Motivo de consulta",
            "observaciones": "Observaciones",
        }
        widgets = {
            "mascota": forms.Select(attrs={"class": "form-select", "id": "id_mascota"}),
            "veterinario": forms.Select(attrs={"class": "form-select"}),
            "fecha_hora": forms.DateTimeInput(attrs={"type": "datetime-local", "class": "form-control"}),
            "motivo": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "observaciones": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.fields['mascota'].queryset = Mascota.objects.filter(activo=True)
        self.fields['veterinario'].queryset = Veterinario.objects.filter(
            perfil__user__is_active=True
        )
        
        if self.instance.pk:
            self.fields['dueno'].initial = self.instance.mascota.dueno
        
        self.order_fields(['dueno', 'mascota', 'veterinario', 'fecha_hora', 'motivo', 'observaciones'])
    
    def clean_fecha_hora(self):
        
        fecha_hora = self.cleaned_data.get('fecha_hora')
        
        if fecha_hora and fecha_hora < timezone.now():
            raise forms.ValidationError('No se puede agendar una cita en el pasado.')
        
        return fecha_hora
    
    def clean_mascota(self):
        mascota = self.cleaned_data.get('mascota')
        
        if not mascota:
            raise forms.ValidationError('Debes seleccionar una mascota para agendar la cita.')
        
        return mascota
    
    def clean(self):
        from datetime import timedelta
        
        cleaned_data = super().clean()
        veterinario = cleaned_data.get('veterinario')
        fecha_hora = cleaned_data.get('fecha_hora')
        mascota = self.cleaned_data.get('mascota')
        
        if not veterinario or not fecha_hora:
            return cleaned_data
        
        if mascota and not mascota.activo:
            raise forms.ValidationError(
                f'No se puede agendar una cita para la mascota {mascota.nombre} porque está inactiva.'
            )
        
        fecha_inicio = fecha_hora.replace(hour=0, minute=0, second=0, microsecond=0)
        fecha_fin = fecha_inicio + timedelta(days=1)
        
        citas_existentes = Cita.objects.filter(
            veterinario=veterinario,
            fecha_hora__gte=fecha_inicio,
            fecha_hora__lt=fecha_fin
        ).exclude(estado='CANCELADO')
        
        if self.instance.pk:
            citas_existentes = citas_existentes.exclude(pk=self.instance.pk)
        
        if citas_existentes.count() >= 8:
            raise forms.ValidationError(
                f'El veterinario {veterinario} ya tiene 8 citas programadas ese día. No puede tener más.'
            )
        
        margen_minutos = 30
        for cita in citas_existentes:
            diferencia_minutos = abs((cita.fecha_hora - fecha_hora).total_seconds() / 60)
            
            if diferencia_minutos < margen_minutos:
                raise forms.ValidationError(
                    f'El veterinario {veterinario} tiene otra cita a las {cita.fecha_hora.strftime("%H:%M")}. '
                    f'Debe haber al menos 30 minutos de separación entre citas.'
                )
        
        if mascota and veterinario:
            citas_activas = Cita.objects.filter(
                mascota=mascota,
                veterinario=veterinario,
                estado='PROGRAMADO'
            )
            
            if self.instance.pk:
                citas_activas = citas_activas.exclude(pk=self.instance.pk)
            
            if citas_activas.exists():
                raise forms.ValidationError(
                    f'La mascota {mascota.nombre} ya tiene una cita activa (sin completar) con el veterinario {veterinario}.'
                )
        
        return cleaned_data

class ConsultaForm(forms.ModelForm):
    class Meta:
        model = Consulta
        fields = ["fecha_consulta", "diagnostico", "tratamiento", "medicamentos", "proxima_cita", "costo"]
        labels = {
            "fecha_consulta": "Fecha de consulta",
            "diagnostico": "Diagnóstico",
            "tratamiento": "Tratamiento prescrito",
            "medicamentos": "Medicamentos",
            "proxima_cita": "Próxima cita (opcional)",
            "costo": "Costo de consulta",
        }
        widgets = {
            "fecha_consulta": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "diagnostico": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "tratamiento": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "medicamentos": forms.Textarea(attrs={"class": "form-control", "rows": 2}),
            "proxima_cita": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "costo": forms.NumberInput(attrs={"class": "form-control", "min": "5000", "max": "200000"}),
        }
    
    def clean_costo(self):
        costo = self.cleaned_data.get('costo')
        if costo and (costo < 5000 or costo > 200000):
            raise forms.ValidationError('El costo debe ser mayor a $5,000 y menor a $200,000.')
        return costo
    
    def clean_proxima_cita(self):
        proxima_cita = self.cleaned_data.get('proxima_cita')
        
        if proxima_cita and proxima_cita < timezone.now().date():
            raise forms.ValidationError('La próxima cita no puede ser en el pasado.')
        
        return proxima_cita
