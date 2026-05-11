from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.urls import reverse_lazy
from .models import CustomUser, Sala, Actividad, Inscripcion
from .forms import (
    ActividadForm, SalaForm,
    CustomUserCreationForm, CustomUserChangeForm, MonitorForm,
)
from .decorators import role_required


def _stub(request, **kwargs):
    from django.http import HttpResponse
    return HttpResponse('stub')


actividades_lista = login_required(_stub)
actividad_crear = login_required(_stub)
actividad_detalle = login_required(_stub)
actividad_editar = login_required(_stub)
actividad_eliminar = login_required(_stub)
inscripciones_lista = login_required(_stub)
inscribir_usuario = login_required(_stub)
cancelar_inscripcion = login_required(_stub)
usuarios_lista = login_required(_stub)
usuario_crear = login_required(_stub)
usuario_detalle = login_required(_stub)
usuario_editar = login_required(_stub)
usuario_eliminar = login_required(_stub)
monitores_lista = login_required(_stub)
monitor_crear = login_required(_stub)
monitor_detalle = login_required(_stub)
monitor_editar = login_required(_stub)
monitor_eliminar = login_required(_stub)
salas_lista = login_required(_stub)
sala_crear = login_required(_stub)
sala_detalle = login_required(_stub)
sala_editar = login_required(_stub)
sala_eliminar = login_required(_stub)
