from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROL_CHOICES = [
        ('admin', 'Personal Administrativo'),
        ('monitor', 'Monitor'),
        ('responsable', 'Responsable de Sala'),
        ('usuario', 'Usuario Inscrito'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='usuario')
    edad = models.PositiveIntegerField(null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    especializacion = models.CharField(max_length=200, null=True, blank=True)

    @property
    def num_actividades(self):
        return self.actividades_impartidas.count()


class Sala(models.Model):
    nombre = models.CharField(max_length=200)
    capacidad = models.PositiveIntegerField()
    ubicacion = models.CharField(max_length=200)
    responsable = models.OneToOneField(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sala_responsable'
    )

    def __str__(self):
        return self.nombre


class Actividad(models.Model):
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=100)
    horario = models.DateTimeField()
    descripcion = models.TextField()
    duracion = models.PositiveIntegerField()
    plazas_disponibles = models.PositiveIntegerField()
    monitor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, related_name='actividades_impartidas'
    )
    sala_principal = models.ForeignKey(
        Sala, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='actividades_principales'
    )
    salas_secundarias = models.ManyToManyField(
        Sala, blank=True, related_name='actividades_secundarias'
    )
    usuarios_inscritos = models.ManyToManyField(
        CustomUser, blank=True,
        related_name='actividades_inscritas',
        through='Inscripcion'
    )

    def __str__(self):
        return self.nombre


class Inscripcion(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['usuario', 'actividad']

    def __str__(self):
        return f'{self.usuario} → {self.actividad}'
