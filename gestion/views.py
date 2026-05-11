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


@login_required
def actividades_lista(request):
    qs = Actividad.objects.select_related('monitor', 'sala_principal').all()
    tipo = request.GET.get('tipo', '')
    monitor_id = request.GET.get('monitor', '')
    if tipo:
        qs = qs.filter(tipo__icontains=tipo)
    if monitor_id:
        qs = qs.filter(monitor_id=monitor_id)
    monitores = CustomUser.objects.filter(rol='monitor')
    return render(request, 'actividades/lista.html', {
        'actividades': qs,
        'monitores': monitores,
        'tipo_filtro': tipo,
        'monitor_filtro': monitor_id,
    })


@login_required
def actividad_detalle(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    ya_inscrito = False
    if request.user.rol == 'usuario':
        ya_inscrito = Inscripcion.objects.filter(
            usuario=request.user, actividad=actividad
        ).exists()
    return render(request, 'actividades/detalle.html', {
        'actividad': actividad,
        'ya_inscrito': ya_inscrito,
    })


@role_required('admin')
def actividad_crear(request):
    form = ActividadForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Actividad creada correctamente.')
        return redirect('actividades_lista')
    return render(request, 'actividades/form.html', {'form': form, 'titulo': 'Nueva Actividad'})


@role_required('admin')
def actividad_editar(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    form = ActividadForm(request.POST or None, instance=actividad)
    if form.is_valid():
        form.save()
        messages.success(request, 'Actividad actualizada.')
        return redirect('actividad_detalle', pk=pk)
    return render(request, 'actividades/form.html', {'form': form, 'titulo': 'Editar Actividad'})


@role_required('admin')
def actividad_eliminar(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if request.method == 'POST':
        actividad.delete()
        messages.success(request, 'Actividad eliminada.')
        return redirect('actividades_lista')
    return render(request, 'actividades/confirmar_eliminar.html', {
        'objeto': actividad, 'tipo': 'actividad',
    })


@role_required('admin', 'monitor')
def inscripciones_lista(request, pk):
    actividad = get_object_or_404(Actividad, pk=pk)
    if request.user.rol == 'monitor' and actividad.monitor != request.user:
        raise PermissionDenied
    inscripciones = Inscripcion.objects.filter(
        actividad=actividad
    ).select_related('usuario')
    return render(request, 'inscripciones/lista.html', {
        'actividad': actividad,
        'inscripciones': inscripciones,
    })


@login_required
def inscribir_usuario(request, pk):
    if request.user.rol not in ['usuario', 'admin']:
        raise PermissionDenied
    actividad = get_object_or_404(Actividad, pk=pk)
    if request.method == 'POST':
        if actividad.plazas_disponibles <= 0:
            messages.error(request, 'No hay plazas disponibles.')
            return redirect('actividad_detalle', pk=pk)
        _, created = Inscripcion.objects.get_or_create(
            usuario=request.user, actividad=actividad
        )
        if created:
            messages.success(request, 'Inscripción realizada.')
        else:
            messages.info(request, 'Ya estabas inscrito.')
        return redirect('actividad_detalle', pk=pk)
    return render(request, 'inscripciones/form.html', {'actividad': actividad})


@login_required
def cancelar_inscripcion(request, pk, uid):
    if request.user.rol == 'usuario' and request.user.pk != uid:
        raise PermissionDenied
    if request.user.rol not in ['usuario', 'admin']:
        raise PermissionDenied
    actividad = get_object_or_404(Actividad, pk=pk)
    inscripcion = get_object_or_404(Inscripcion, actividad=actividad, usuario_id=uid)
    if request.method == 'POST':
        inscripcion.delete()
        messages.success(request, 'Inscripción cancelada.')
        return redirect('actividad_detalle', pk=pk)
    return render(request, 'inscripciones/confirmar_cancelar.html', {
        'inscripcion': inscripcion,
        'actividad': actividad,
    })


@role_required('admin')
def usuarios_lista(request):
    actividad_id = request.GET.get('actividad', '')
    qs = CustomUser.objects.all()
    if actividad_id:
        qs = qs.filter(actividades_inscritas__id=actividad_id)
    return render(request, 'usuarios/lista.html', {
        'usuarios': qs,
        'actividad_filtro': actividad_id,
    })


@role_required('admin')
def usuario_crear(request):
    form = CustomUserCreationForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Usuario creado.')
        return redirect('usuarios_lista')
    return render(request, 'usuarios/form.html', {'form': form, 'titulo': 'Nuevo Usuario'})


@login_required
def usuario_detalle(request, pk):
    if request.user.rol == 'usuario' and request.user.pk != pk:
        raise PermissionDenied
    if request.user.rol not in ['admin', 'usuario']:
        raise PermissionDenied
    usuario = get_object_or_404(CustomUser, pk=pk)
    return render(request, 'usuarios/detalle.html', {'usuario': usuario})


@login_required
def usuario_editar(request, pk):
    if request.user.rol == 'usuario' and request.user.pk != pk:
        raise PermissionDenied
    if request.user.rol not in ['admin', 'usuario']:
        raise PermissionDenied
    usuario = get_object_or_404(CustomUser, pk=pk)
    form = CustomUserChangeForm(request.POST or None, instance=usuario)
    if form.is_valid():
        form.save()
        messages.success(request, 'Perfil actualizado.')
        return redirect('usuario_detalle', pk=pk)
    return render(request, 'usuarios/form.html', {'form': form, 'titulo': 'Editar Usuario'})


@role_required('admin')
def usuario_eliminar(request, pk):
    usuario = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        usuario.delete()
        messages.success(request, 'Usuario eliminado.')
        return redirect('usuarios_lista')
    return render(request, 'usuarios/confirmar_eliminar.html', {
        'objeto': usuario, 'tipo': 'usuario',
    })
@role_required('admin', 'monitor')
def monitores_lista(request):
    monitores = CustomUser.objects.filter(rol='monitor')
    return render(request, 'monitores/lista.html', {'monitores': monitores})


@role_required('admin')
def monitor_crear(request):
    form = MonitorForm(request.POST or None)
    if form.is_valid():
        monitor = form.save(commit=False)
        monitor.rol = 'monitor'
        monitor.save()
        messages.success(request, 'Monitor creado.')
        return redirect('monitores_lista')
    return render(request, 'monitores/form.html', {'form': form, 'titulo': 'Nuevo Monitor'})


@role_required('admin', 'monitor')
def monitor_detalle(request, pk):
    monitor = get_object_or_404(CustomUser, pk=pk, rol='monitor')
    return render(request, 'monitores/detalle.html', {'monitor': monitor})


@login_required
def monitor_editar(request, pk):
    monitor = get_object_or_404(CustomUser, pk=pk, rol='monitor')
    if request.user.rol == 'monitor' and request.user.pk != pk:
        raise PermissionDenied
    if request.user.rol not in ['admin', 'monitor']:
        raise PermissionDenied
    form = MonitorForm(request.POST or None, instance=monitor)
    if form.is_valid():
        form.save()
        messages.success(request, 'Monitor actualizado.')
        return redirect('monitor_detalle', pk=pk)
    return render(request, 'monitores/form.html', {'form': form, 'titulo': 'Editar Monitor'})


@role_required('admin')
def monitor_eliminar(request, pk):
    monitor = get_object_or_404(CustomUser, pk=pk, rol='monitor')
    if request.method == 'POST':
        monitor.delete()
        messages.success(request, 'Monitor eliminado.')
        return redirect('monitores_lista')
    return render(request, 'monitores/confirmar_eliminar.html', {
        'objeto': monitor, 'tipo': 'monitor',
    })
@login_required
def salas_lista(request):
    if request.user.rol not in ['admin', 'responsable']:
        raise PermissionDenied
    if request.user.rol == 'admin':
        salas = Sala.objects.select_related('responsable').all()
    else:
        salas = Sala.objects.filter(responsable=request.user)
    return render(request, 'salas/lista.html', {'salas': salas})


@role_required('admin')
def sala_crear(request):
    form = SalaForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, 'Sala creada.')
        return redirect('salas_lista')
    return render(request, 'salas/form.html', {'form': form, 'titulo': 'Nueva Sala'})


@login_required
def sala_detalle(request, pk):
    if request.user.rol not in ['admin', 'responsable']:
        raise PermissionDenied
    sala = get_object_or_404(Sala, pk=pk)
    if request.user.rol == 'responsable' and sala.responsable != request.user:
        raise PermissionDenied
    return render(request, 'salas/detalle.html', {'sala': sala})


@role_required('admin')
def sala_editar(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    form = SalaForm(request.POST or None, instance=sala)
    if form.is_valid():
        form.save()
        messages.success(request, 'Sala actualizada.')
        return redirect('sala_detalle', pk=pk)
    return render(request, 'salas/form.html', {'form': form, 'titulo': 'Editar Sala'})


@role_required('admin')
def sala_eliminar(request, pk):
    sala = get_object_or_404(Sala, pk=pk)
    if request.method == 'POST':
        sala.delete()
        messages.success(request, 'Sala eliminada.')
        return redirect('salas_lista')
    return render(request, 'salas/confirmar_eliminar.html', {
        'objeto': sala, 'tipo': 'sala',
    })
