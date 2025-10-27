from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django_mysql.models import EnumField
from django.conf import settings


# ── Validadores básicos
rut_valido = RegexValidator(r'^[0-9A-Za-z.\-]{7,12}$', 'RUT/DNI inválido')
telefono_valido = RegexValidator(r'^\+?[0-9]{8,15}$', 'Teléfono inválido')

# Create your models here.

class Perfil(models.Model):
    tipo = EnumField(
        choices=['ADMINISTRADOR', 'VETERINARIO', 'RECEPCIONISTA', 'CLIENTE'],  # ← corregido
        default='CLIENTE'
    )
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='perfil')
    rut = models.CharField(max_length=12, unique=True)
    telefono = models.CharField(max_length=15)

    def __str__(self):
        return f"{self.user.username} ({self.tipo})"

    class Meta:
        ordering = ['user__username']


class Cliente(models.Model):
    perfil = models.OneToOneField(Perfil, on_delete=models.CASCADE, related_name='cliente')
    nombre = models.CharField(max_length=45)
    apellido = models.CharField(max_length=45)
    direccion = models.CharField(max_length=100, blank=True)
    fecha_registro = models.DateField(auto_now_add=True)

    def clean(self):
        # si aún no le asignan perfil, no valides (se valida al guardar con perfil)
        if not self.perfil_id:
            return
        if self.perfil.tipo != 'CLIENTE':
            raise ValidationError('El perfil asociado debe ser de tipo Cliente.')

    def __str__(self):
        return f'{self.nombre} {self.apellido}'

    class Meta:
        ordering = ['apellido', 'nombre']


class Veterinario(models.Model):
    perfil = models.OneToOneField(Perfil, on_delete=models.CASCADE, related_name='veterinario')
    nombre = models.CharField(max_length=45)
    apellido = models.CharField(max_length=45)
    especialidad = models.CharField(max_length=100)
    licencia_profesional = models.CharField(max_length=100, unique=True)
    telefono_laboral = models.CharField(max_length=15, blank=True)

    def clean(self):
        # evita acceder a self.perfil si no está puesto
        if not self.perfil_id:
            return
        if self.perfil.tipo != 'VETERINARIO':
            raise ValidationError('El perfil asociado debe ser de tipo Veterinario.')

    def __str__(self):
        return f'Dr(a). {self.nombre} {self.apellido}'

    class Meta:
        ordering = ['apellido', 'nombre']


class Mascota(models.Model):

    especie = EnumField(
        choices=['PERRO', 'GATO', 'CONEJO', 'AVE', 'OTRO'],
    )
    sexo = EnumField(
        choices=['M', 'F']
    )

    dueno = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='mascotas')
    nombre = models.CharField(max_length=45)
    raza = models.CharField(max_length=45, blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    color = models.CharField(max_length=45, blank=True)
    activo = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.nombre} ({self.especie})'

    class Meta:
        ordering = ['dueno__apellido', 'nombre']


class Cita(models.Model):
    
    estado = EnumField(
    choices=['PROGRAMADO', 'COMPLETADO', 'CANCELADO'],  # corregido
    default='PROGRAMADO'
)

    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='citas')
    veterinario = models.ForeignKey(Veterinario, on_delete=models.PROTECT, related_name='citas')
    fecha_hora = models.DateTimeField()
    motivo = models.CharField(max_length=250)
    observaciones = models.CharField(max_length=250, blank=True)

def clean(self):
    # 0) Si no hay mascota asignada, saltamos las validaciones (se valida en el formulario)
    if not self.mascota_id:
        return
    
    # 0.1) Si no hay fecha, no validamos más
    if not self.fecha_hora:
        return

    # Normalizar tz (por si viene naive)
    cita_dt = self.fecha_hora
    if timezone.is_naive(cita_dt):
        cita_dt = timezone.make_aware(cita_dt, timezone.get_current_timezone())

    # 1) No en el pasado (si está programada)
    if self.estado == 'PROGRAMADO' and cita_dt < timezone.localtime():
        raise ValidationError({'fecha_hora': 'No se puede agendar una cita en el pasado.'})

    # 2) Mascota activa
    try:
        if self.mascota and not self.mascota.activo:
            raise ValidationError({'mascota': 'No se puede agendar una cita para una mascota inactiva.'})
    except:
        pass

    # 3) Solo 1 cita activa (sin completar/cancelar) por mascota+veterinario
    if self.mascota and self.veterinario and self.estado == 'PROGRAMADO':
        qs = Cita.objects.filter(
            mascota=self.mascota,
            veterinario=self.veterinario,
            estado='PROGRAMADO',
        )
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError('La mascota ya tiene una cita activa con este veterinario.')

    # 4) Máximo 8 citas PROGRAMADAS por día y veterinario
    if self.veterinario and self.estado == 'PROGRAMADO':
        dia = cita_dt.date()
        inicio_dia = timezone.make_aware(
            timezone.datetime.combine(dia, timezone.datetime.min.time()),
            timezone.get_current_timezone()
        )
        fin_dia = timezone.make_aware(
            timezone.datetime.combine(dia, timezone.datetime.max.time()),
            timezone.get_current_timezone()
        )
        qs_dia = Cita.objects.filter(
            veterinario=self.veterinario,
            estado='PROGRAMADO',
            fecha_hora__range=(inicio_dia, fin_dia)
        )
        if self.pk:
            qs_dia = qs_dia.exclude(pk=self.pk)
        if qs_dia.count() >= 8:
            raise ValidationError({'fecha_hora': 'El veterinario ya tiene 8 citas programadas en ese día.'})

    def __str__(self):
        return f'Cita {self.estado} - {self.mascota} con {self.veterinario}'

    class Meta:
        ordering = ['-fecha_hora']
        indexes = [models.Index(fields=['fecha_hora'])]


class Consulta(models.Model):
    cita = models.OneToOneField(Cita, on_delete=models.PROTECT, related_name='consulta')
    fecha_consulta = models.DateField()
    diagnostico = models.CharField(max_length=250)
    tratamiento = models.CharField(max_length=250, blank=True)
    medicamentos = models.CharField(max_length=250, blank=True)
    proxima_cita = models.DateField(null=True, blank=True)
    costo = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Consulta de {self.cita.mascota} el {self.fecha_consulta}'

    class Meta:
        ordering = ['-fecha_consulta']


class Recepcionista(models.Model):
    perfil = models.OneToOneField(Perfil, on_delete=models.CASCADE, related_name='recepcionista')
    nombre = models.CharField(max_length=45)
    apellido = models.CharField(max_length=45)
    telefono = models.CharField(max_length=15, blank=True)

    def clean(self):
        if not self.perfil_id:
            return
        if self.perfil.tipo != 'RECEPCIONISTA':
            raise ValidationError('El perfil asociado debe ser de tipo Recepcionista.')

    def __str__(self):
        return f'{self.nombre} {self.apellido}'

    class Meta:
        ordering = ['apellido', 'nombre']
