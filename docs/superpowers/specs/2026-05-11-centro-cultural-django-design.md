# Diseño: Plataforma de Gestión de Actividades — Centro Cultural

## Contexto

Práctica final de la asignatura Arquitectura del Software (Universidad Pontificia de Salamanca).
Autores: Gonzalo Gardón Martín – Álvaro Criado García.

El objetivo es obtener la **máxima nota (10 + 1 punto extra)** implementando una plataforma Django para digitalizar la gestión de actividades, monitores, salas e inscripciones de un centro cultural municipal.

La **parte teórica** (4 puntos) ya está completada en `MemoriaArquitecturaSoftware.pdf`:
- Diagramas C4 (Contexto, Contenedores, Componentes) — 2,0 pts
- Patrón Observer justificado — 1,0 pt
- MVC vs MVT explicado — 1,0 pt

Este documento cubre el **diseño de la parte práctica** (6 puntos + extras).

---

## Decisiones clave

| Decisión | Elección | Justificación |
|---|---|---|
| Arquitectura | MVT (Django nativo) | Coincide con la teoría del PDF |
| App Django | Una sola: `gestion` | El PDF define arquitectura de app única |
| Vistas | FBV (Function-Based Views) | Más explícitas y trazables en evaluación académica |
| CSS | Tailwind via CDN | Diseño moderno sin paso de build; suma puntos extra |
| Auth | Custom User + rol field | Más directo que Django Groups para 4 roles |
| DB | SQLite (desarrollo) | Sin instalación; el PDF justifica migración a PostgreSQL en producción |
| Patrón Observer | Django signals (`post_save`, `post_delete`) | Implementación idiomática descrita en el PDF |

---

## Modelo de datos

### CustomUser (extiende AbstractUser)

```python
class CustomUser(AbstractUser):
    ROL_CHOICES = [
        ('admin', 'Personal Administrativo'),
        ('monitor', 'Monitor'),
        ('responsable', 'Responsable de Sala'),
        ('usuario', 'Usuario Inscrito'),
    ]
    rol = models.CharField(max_length=20, choices=ROL_CHOICES, default='usuario')
    # Campos para rol=usuario
    edad = models.PositiveIntegerField(null=True, blank=True)
    telefono = models.CharField(max_length=20, null=True, blank=True)
    # Campos para rol=monitor
    especializacion = models.CharField(max_length=200, null=True, blank=True)

    @property
    def num_actividades(self):
        return self.actividades_impartidas.count()  # solo monitores
```

### Sala

```python
class Sala(models.Model):
    nombre = models.CharField(max_length=200)
    capacidad = models.PositiveIntegerField()
    ubicacion = models.CharField(max_length=200)
    responsable = models.OneToOneField(
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sala_responsable'
    )  # Relación 1:1 — Sala ↔ ResponsableSala
```

### Actividad

```python
class Actividad(models.Model):
    nombre = models.CharField(max_length=200)
    tipo = models.CharField(max_length=100)
    horario = models.DateTimeField()
    descripcion = models.TextField()
    duracion = models.PositiveIntegerField()       # en minutos
    plazas_disponibles = models.PositiveIntegerField()
    monitor = models.ForeignKey(
        CustomUser, on_delete=models.SET_NULL,
        null=True, related_name='actividades_impartidas'
    )  # Relación 1:N — un monitor imparte muchas actividades
    sala_principal = models.ForeignKey(
        Sala, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='actividades_principales'
    )
    salas_secundarias = models.ManyToManyField(
        Sala, blank=True, related_name='actividades_secundarias'
    )  # Relación N:N — actividad ↔ salas secundarias
    usuarios_inscritos = models.ManyToManyField(
        CustomUser, blank=True,
        related_name='actividades_inscritas',
        through='Inscripcion'
    )  # Relación N:N — usuario ↔ actividad
```

### Inscripcion (through model)

```python
class Inscripcion(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    actividad = models.ForeignKey(Actividad, on_delete=models.CASCADE)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['usuario', 'actividad']
```

### Mapa de relaciones

```
CustomUser(usuario) ←—— N:N (through Inscripcion) ——→ Actividad
Actividad          ←—— N:1 ——→ CustomUser(monitor)
Sala               ←—— 1:1 ——→ CustomUser(responsable)
Actividad          ←—— N:N ——→ Sala (sala_principal FK + salas_secundarias M2M)
```

---

## Autenticación y roles

**settings.py**
```python
AUTH_USER_MODEL = 'gestion.CustomUser'
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'
```

**gestion/decorators.py** — decorador `@role_required`
```python
def role_required(*roles):
    def decorator(view_func):
        @login_required
        def wrapped(request, *args, **kwargs):
            if request.user.rol not in roles:
                raise PermissionDenied
            return view_func(request, *args, **kwargs)
        return wrapped
    return decorator
```

### Matriz de permisos

| Sección | admin | monitor | responsable | usuario |
|---|---|---|---|---|
| Actividades CRUD | ✅ | 👁️ sus actividades | 👁️ ver | 👁️ ver |
| Usuarios CRUD | ✅ | ❌ | ❌ | 👁️ su perfil |
| Monitores CRUD | ✅ | 👁️ su perfil | ❌ | ❌ |
| Salas CRUD | ✅ | ❌ | 👁️ sus salas | ❌ |
| Inscripciones | ✅ gestión total | 👁️ sus actividades | ❌ | ✅ las suyas |

---

## Endpoints (26 en total)

### Auth
| URL | Vista | Rol |
|---|---|---|
| `/login/` | LoginView | público |
| `/logout/` | LogoutView | autenticado |

### Actividades
| URL | Vista | Rol |
|---|---|---|
| `/actividades/` | actividades_lista | todos |
| `/actividades/nueva/` | actividad_crear | admin |
| `/actividades/<id>/` | actividad_detalle | todos |
| `/actividades/<id>/editar/` | actividad_editar | admin |
| `/actividades/<id>/eliminar/` | actividad_eliminar | admin |

### Inscripciones
| URL | Vista | Rol |
|---|---|---|
| `/actividades/<id>/inscripciones/` | inscripciones_lista | admin, monitor |
| `/actividades/<id>/inscribir/` | inscribir_usuario | usuario, admin |
| `/actividades/<id>/inscripciones/<uid>/eliminar/` | cancelar_inscripcion | usuario, admin |

### Usuarios
| URL | Vista | Rol |
|---|---|---|
| `/usuarios/` | usuarios_lista | admin |
| `/usuarios/nuevo/` | usuario_crear | admin |
| `/usuarios/<id>/` | usuario_detalle | admin, usuario (propio) |
| `/usuarios/<id>/editar/` | usuario_editar | admin, usuario (propio) |
| `/usuarios/<id>/eliminar/` | usuario_eliminar | admin |

### Monitores
| URL | Vista | Rol |
|---|---|---|
| `/monitores/` | monitores_lista | admin, monitor |
| `/monitores/nuevo/` | monitor_crear | admin |
| `/monitores/<id>/` | monitor_detalle | admin, monitor |
| `/monitores/<id>/editar/` | monitor_editar | admin, monitor (propio) |
| `/monitores/<id>/eliminar/` | monitor_eliminar | admin |

### Salas
| URL | Vista | Rol |
|---|---|---|
| `/salas/` | salas_lista | admin, responsable |
| `/salas/nueva/` | sala_crear | admin |
| `/salas/<id>/` | sala_detalle | admin, responsable |
| `/salas/<id>/editar/` | sala_editar | admin |
| `/salas/<id>/eliminar/` | sala_eliminar | admin |

### Filtros GET
| URL | Parámetro | Comportamiento |
|---|---|---|
| `/actividades/?tipo=danza` | `tipo` | filtra por tipo de actividad |
| `/actividades/?monitor=3` | `monitor` | filtra por ID de monitor |
| `/usuarios/?actividad=5` | `actividad` | usuarios inscritos en actividad |

---

## Patrón Observer — signals.py

```python
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Inscripcion

@receiver(post_save, sender=Inscripcion)
def actualizar_plazas_al_inscribir(sender, instance, created, **kwargs):
    if created:
        actividad = instance.actividad
        actividad.plazas_disponibles = max(0, actividad.plazas_disponibles - 1)
        actividad.save(update_fields=['plazas_disponibles'])

@receiver(post_delete, sender=Inscripcion)
def restaurar_plazas_al_cancelar(sender, instance, **kwargs):
    actividad = instance.actividad
    actividad.plazas_disponibles += 1
    actividad.save(update_fields=['plazas_disponibles'])
```

La vista de inscripción solo crea/elimina el objeto `Inscripcion`. La lógica de plazas vive en las signals — implementación directa del patrón Observer descrito en el PDF.

---

## Estructura de archivos

```
centro_cultural/          ← proyecto Django
├── settings.py
├── urls.py               ← incluye gestion.urls + auth urls
└── wsgi.py

gestion/                  ← única app Django
├── models.py             ← CustomUser, Sala, Actividad, Inscripcion
├── views.py              ← todas las FBV (26 endpoints)
├── forms.py              ← ModelForms para cada entidad
├── urls.py               ← 26 URL patterns
├── signals.py            ← Observer (post_save, post_delete)
├── decorators.py         ← @role_required
├── admin.py              ← registro en Django Admin
├── apps.py               ← conecta signals en ready()
└── templates/
    ├── base.html         ← navbar Tailwind (role-aware) + bloques
    ├── auth/
    │   └── login.html
    ├── actividades/
    │   ├── lista.html · detalle.html · form.html · confirmar_eliminar.html
    ├── inscripciones/
    │   ├── lista.html · form.html
    ├── usuarios/
    │   ├── lista.html · detalle.html · form.html · confirmar_eliminar.html
    ├── monitores/
    │   ├── lista.html · detalle.html · form.html · confirmar_eliminar.html
    └── salas/
        ├── lista.html · detalle.html · form.html · confirmar_eliminar.html

manage.py
db.sqlite3
requirements.txt          ← django, (sin dependencias externas)
```

---

## Puntuación estimada

| Criterio | Pts | Cubierto por |
|---|---|---|
| Arquitectura teórica C4 | 2,0 | PDF ya entregado |
| Patrón de diseño | 1,0 | PDF ya entregado |
| MVC vs MVT | 1,0 | PDF ya entregado |
| Modelado relaciones (1-1, 1-N, N-N) | 1,5 | models.py |
| Endpoints funcionalidad completa | 2,0 | views.py + urls.py |
| Filtros de búsqueda | 1,0 | views.py (parámetros GET) |
| Templates funcionales | 1,0 | 17 templates Tailwind |
| **Extra**: diseño visual cuidado | +0,5 | Tailwind cards + gradientes |
| **Extra**: GitHub con ramas y commits | +0,5 | git flow durante desarrollo |
| **TOTAL** | **10,5** | |
