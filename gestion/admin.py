from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Sala, Actividad, Inscripcion


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'rol', 'first_name', 'last_name']
    list_filter = ['rol']
    fieldsets = UserAdmin.fieldsets + (
        ('Centro Cultural', {'fields': ('rol', 'edad', 'telefono', 'especializacion')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Centro Cultural', {'fields': ('rol', 'edad', 'telefono', 'especializacion')}),
    )


@admin.register(Sala)
class SalaAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'capacidad', 'ubicacion', 'responsable']


@admin.register(Actividad)
class ActividadAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'tipo', 'horario', 'plazas_disponibles', 'monitor', 'sala_principal']
    list_filter = ['tipo']


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'actividad', 'fecha_inscripcion']
