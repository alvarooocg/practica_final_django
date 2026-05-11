from django.urls import path
from . import views

urlpatterns = [
    # Actividades
    path('actividades/', views.actividades_lista, name='actividades_lista'),
    path('actividades/nueva/', views.actividad_crear, name='actividad_crear'),
    path('actividades/<int:pk>/', views.actividad_detalle, name='actividad_detalle'),
    path('actividades/<int:pk>/editar/', views.actividad_editar, name='actividad_editar'),
    path('actividades/<int:pk>/eliminar/', views.actividad_eliminar, name='actividad_eliminar'),
    # Inscripciones
    path('actividades/<int:pk>/inscripciones/', views.inscripciones_lista, name='inscripciones_lista'),
    path('actividades/<int:pk>/inscribir/', views.inscribir_usuario, name='inscribir_usuario'),
    path('actividades/<int:pk>/inscripciones/<int:uid>/eliminar/', views.cancelar_inscripcion, name='cancelar_inscripcion'),
    # Usuarios
    path('usuarios/', views.usuarios_lista, name='usuarios_lista'),
    path('usuarios/nuevo/', views.usuario_crear, name='usuario_crear'),
    path('usuarios/<int:pk>/', views.usuario_detalle, name='usuario_detalle'),
    path('usuarios/<int:pk>/editar/', views.usuario_editar, name='usuario_editar'),
    path('usuarios/<int:pk>/eliminar/', views.usuario_eliminar, name='usuario_eliminar'),
    # Monitores
    path('monitores/', views.monitores_lista, name='monitores_lista'),
    path('monitores/nuevo/', views.monitor_crear, name='monitor_crear'),
    path('monitores/<int:pk>/', views.monitor_detalle, name='monitor_detalle'),
    path('monitores/<int:pk>/editar/', views.monitor_editar, name='monitor_editar'),
    path('monitores/<int:pk>/eliminar/', views.monitor_eliminar, name='monitor_eliminar'),
    # Salas
    path('salas/', views.salas_lista, name='salas_lista'),
    path('salas/nueva/', views.sala_crear, name='sala_crear'),
    path('salas/<int:pk>/', views.sala_detalle, name='sala_detalle'),
    path('salas/<int:pk>/editar/', views.sala_editar, name='sala_editar'),
    path('salas/<int:pk>/eliminar/', views.sala_eliminar, name='sala_eliminar'),
]
