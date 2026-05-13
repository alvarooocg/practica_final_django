# Plataforma de Gestión de Actividades — Centro Cultural Municipal

**Práctica Final — Arquitectura del Software**  
Universidad Pontificia de Salamanca  
Autores: Gonzalo Gardón Martín · Álvaro Criado García

---

## Índice

1. [Descripción del proyecto](#descripción-del-proyecto)
2. [Arquitectura del sistema](#arquitectura-del-sistema)
3. [Modelo de datos](#modelo-de-datos)
4. [Patrón Observer](#patrón-observer)
5. [Autenticación y control de acceso](#autenticación-y-control-de-acceso)
6. [Endpoints y filtros](#endpoints-y-filtros)
7. [Templates](#templates)
8. [Instalación y puesta en marcha](#instalación-y-puesta-en-marcha)
9. [Tests](#tests)
10. [Estructura del proyecto](#estructura-del-proyecto)

---

## Descripción del proyecto

Aplicación web Django para digitalizar la gestión de actividades culturales de un centro municipal. Permite administrar actividades, monitores, salas e inscripciones a través de cuatro roles de usuario diferenciados.

**Tecnologías utilizadas:**
- Python 3.x + Django 5.x
- SQLite (base de datos de desarrollo)
- Tailwind CSS (via CDN, sin paso de build)

---

## Arquitectura del sistema

El proyecto sigue el patrón **MVT (Model–View–Template)** propio de Django, que es la variante del patrón MVC adaptada al framework:

| Capa | MVC clásico | Django MVT |
|---|---|---|
| Lógica de negocio y datos | Model | **Model** (`models.py`) |
| Gestión de peticiones | Controller | **View** (`views.py`) |
| Presentación | View | **Template** (`templates/`) |

En Django el "controlador" es el propio framework (URL dispatcher + ORM), y el desarrollador escribe Models, Views (funciones que procesan la petición) y Templates (HTML que se renderiza). Esta equivalencia se desarrolla en detalle en la memoria teórica (`MemoriaArquitecturaSoftware.pdf`), junto con los diagramas C4 (Contexto, Contenedores y Componentes).

**Estructura de la aplicación:**

```
centro_cultural/     ← Proyecto Django (configuración, URL raíz)
└── gestion/         ← Única app Django (toda la lógica de negocio)
    ├── models.py
    ├── views.py
    ├── urls.py
    ├── forms.py
    ├── signals.py   ← Patrón Observer
    ├── decorators.py
    └── templates/
```

Se optó por una **única app** (`gestion`) en coherencia con los diagramas C4 de la memoria, que modelan el sistema como un único componente de aplicación.

---

## Modelo de datos

El modelo implementa los tres tipos de relación requeridos: **1:1**, **1:N** y **N:N**.

### CustomUser

Extiende `AbstractUser` de Django añadiendo un campo de rol y datos específicos por perfil:

```python
class CustomUser(AbstractUser):
    ROL_CHOICES = [
        ('admin',       'Personal Administrativo'),
        ('monitor',     'Monitor'),
        ('responsable', 'Responsable de Sala'),
        ('usuario',     'Usuario Inscrito'),
    ]
    rol             = models.CharField(max_length=20, choices=ROL_CHOICES, default='usuario')
    edad            = models.PositiveIntegerField(null=True, blank=True)   # rol=usuario
    telefono        = models.CharField(max_length=20, null=True, blank=True)
    especializacion = models.CharField(max_length=200, null=True, blank=True)  # rol=monitor

    @property
    def num_actividades(self):
        return self.actividades_impartidas.count()
```

### Sala

```python
class Sala(models.Model):
    nombre     = models.CharField(max_length=200)
    capacidad  = models.PositiveIntegerField()
    ubicacion  = models.CharField(max_length=200)
    responsable = models.OneToOneField(          # ← Relación 1:1
        CustomUser, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='sala_responsable'
    )
```

### Actividad

```python
class Actividad(models.Model):
    nombre             = models.CharField(max_length=200)
    tipo               = models.CharField(max_length=100)
    horario            = models.DateTimeField()
    descripcion        = models.TextField()
    duracion           = models.PositiveIntegerField()        # minutos
    plazas_disponibles = models.PositiveIntegerField()
    monitor = models.ForeignKey(                              # ← Relación 1:N
        CustomUser, on_delete=models.SET_NULL,
        null=True, related_name='actividades_impartidas'
    )
    sala_principal = models.ForeignKey(                       # ← Relación 1:N
        Sala, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='actividades_principales'
    )
    salas_secundarias = models.ManyToManyField(               # ← Relación N:N
        Sala, blank=True, related_name='actividades_secundarias'
    )
    usuarios_inscritos = models.ManyToManyField(              # ← Relación N:N
        CustomUser, blank=True,
        related_name='actividades_inscritas',
        through='Inscripcion'
    )
```

### Inscripcion (tabla intermedia)

Modelo `through` que añade metadatos a la relación N:N entre usuarios y actividades:

```python
class Inscripcion(models.Model):
    usuario           = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    actividad         = models.ForeignKey(Actividad,  on_delete=models.CASCADE)
    fecha_inscripcion = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['usuario', 'actividad']
```

### Mapa de relaciones

```
CustomUser (usuario)  ←── N:N (through Inscripcion) ──→  Actividad
Actividad             ←── N:1 ──────────────────────→  CustomUser (monitor)
Sala                  ←── 1:1 ──────────────────────→  CustomUser (responsable)
Actividad             ←── N:1 ──────────────────────→  Sala (sala_principal)
Actividad             ←── N:N ──────────────────────→  Sala (salas_secundarias)
```

---

## Patrón Observer

El proyecto implementa el **patrón Observer** usando el sistema de señales (`signals`) de Django. Cuando se crea o elimina una `Inscripcion`, las señales notifican automáticamente a la actividad para actualizar sus plazas disponibles, sin que la vista necesite conocer este mecanismo.

```python
# gestion/signals.py

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

**Correspondencia con el patrón:**

| Rol en Observer | Implementación Django |
|---|---|
| Sujeto (Subject) | Modelo `Inscripcion` |
| Evento | `post_save` / `post_delete` |
| Observador (Observer) | Funciones receptor (`@receiver`) |
| Notificación | Llamada automática por el ORM de Django |

Las señales se registran en `gestion/apps.py` dentro del método `ready()`, garantizando que estén activas desde el arranque:

```python
class GestionConfig(AppConfig):
    name = 'gestion'

    def ready(self):
        import gestion.signals  # noqa: F401
```

---

## Autenticación y control de acceso

### Roles

| Rol | Descripción |
|---|---|
| `admin` | Personal administrativo. Acceso completo a todos los módulos. |
| `monitor` | Imparte actividades. Ve sus propias actividades e inscripciones. |
| `responsable` | Gestiona las salas asignadas. |
| `usuario` | Ciudadano inscrito. Se inscribe/cancela en actividades. |

### Decorador `@role_required`

Implementado en `gestion/decorators.py`. Combina `@login_required` con comprobación de rol, lanzando `PermissionDenied` (HTTP 403) si el usuario no tiene el rol necesario:

```python
@role_required('admin', 'monitor')
def inscripciones_lista(request, pk):
    ...
```

### Matriz de permisos

| Módulo | admin | monitor | responsable | usuario |
|---|:---:|:---:|:---:|:---:|
| Actividades — CRUD | ✅ | 👁 ver | 👁 ver | 👁 ver |
| Actividades — inscribir | ✅ | ❌ | ❌ | ✅ |
| Inscripciones — lista | ✅ | 👁 las suyas | ❌ | ❌ |
| Inscripciones — cancelar | ✅ | ❌ | ❌ | ✅ las suyas |
| Usuarios — CRUD | ✅ | ❌ | ❌ | 👁 su perfil |
| Monitores — CRUD | ✅ | 👁 su perfil | ❌ | ❌ |
| Salas — CRUD | ✅ | ❌ | 👁 las suyas | ❌ |

---

## Endpoints y filtros

La aplicación expone **25 URLs** más los endpoints de autenticación.

### Autenticación

| Método | URL | Descripción |
|---|---|---|
| GET/POST | `/login/` | Formulario de acceso |
| POST | `/logout/` | Cierre de sesión |
| — | `/` | Redirección a `/actividades/` |

### Actividades

| Método | URL | Vista | Roles |
|---|---|---|---|
| GET | `/actividades/` | `actividades_lista` | Todos |
| GET/POST | `/actividades/nueva/` | `actividad_crear` | admin |
| GET | `/actividades/<id>/` | `actividad_detalle` | Todos |
| GET/POST | `/actividades/<id>/editar/` | `actividad_editar` | admin |
| GET/POST | `/actividades/<id>/eliminar/` | `actividad_eliminar` | admin |

### Inscripciones

| Método | URL | Vista | Roles |
|---|---|---|---|
| GET | `/actividades/<id>/inscripciones/` | `inscripciones_lista` | admin, monitor |
| POST | `/actividades/<id>/inscribir/` | `inscribir_usuario` | usuario, admin |
| GET/POST | `/actividades/<id>/inscripciones/<uid>/eliminar/` | `cancelar_inscripcion` | usuario, admin |

### Usuarios

| Método | URL | Vista | Roles |
|---|---|---|---|
| GET | `/usuarios/` | `usuarios_lista` | admin |
| GET/POST | `/usuarios/nuevo/` | `usuario_crear` | admin |
| GET | `/usuarios/<id>/` | `usuario_detalle` | admin, usuario (propio) |
| GET/POST | `/usuarios/<id>/editar/` | `usuario_editar` | admin, usuario (propio) |
| GET/POST | `/usuarios/<id>/eliminar/` | `usuario_eliminar` | admin |

### Monitores

| Método | URL | Vista | Roles |
|---|---|---|---|
| GET | `/monitores/` | `monitores_lista` | admin, monitor |
| GET/POST | `/monitores/nuevo/` | `monitor_crear` | admin |
| GET | `/monitores/<id>/` | `monitor_detalle` | admin, monitor |
| GET/POST | `/monitores/<id>/editar/` | `monitor_editar` | admin, monitor (propio) |
| GET/POST | `/monitores/<id>/eliminar/` | `monitor_eliminar` | admin |

### Salas

| Método | URL | Vista | Roles |
|---|---|---|---|
| GET | `/salas/` | `salas_lista` | admin, responsable |
| GET/POST | `/salas/nueva/` | `sala_crear` | admin |
| GET | `/salas/<id>/` | `sala_detalle` | admin, responsable |
| GET/POST | `/salas/<id>/editar/` | `sala_editar` | admin |
| GET/POST | `/salas/<id>/eliminar/` | `sala_eliminar` | admin |

### Filtros de búsqueda (parámetros GET)

La vista de listado de actividades y usuarios admite filtros por parámetros en la URL:

| URL | Parámetro | Comportamiento |
|---|---|---|
| `/actividades/?tipo=danza` | `tipo` | Filtra actividades por tipo |
| `/actividades/?monitor=3` | `monitor` | Filtra actividades por ID de monitor |
| `/usuarios/?actividad=5` | `actividad` | Lista usuarios inscritos en una actividad |

---

## Templates

La aplicación cuenta con **21 templates** organizados por módulo, todos heredando de `base.html`.

| Template | Descripción |
|---|---|
| `base.html` | Navbar Tailwind con menú adaptado al rol del usuario |
| `auth/login.html` | Formulario de inicio de sesión |
| `actividades/lista.html` | Listado con filtros tipo/monitor |
| `actividades/detalle.html` | Ficha de actividad con botón de inscripción |
| `actividades/form.html` | Formulario crear/editar (compartido) |
| `actividades/confirmar_eliminar.html` | Confirmación antes de borrar |
| `inscripciones/lista.html` | Inscritos en una actividad |
| `inscripciones/form.html` | Confirmación de inscripción |
| `inscripciones/confirmar_cancelar.html` | Confirmación de cancelación |
| `usuarios/lista.html` | Listado de usuarios (filtrable por actividad) |
| `usuarios/detalle.html` | Perfil de usuario |
| `usuarios/form.html` | Formulario crear/editar usuario |
| `usuarios/confirmar_eliminar.html` | Confirmación antes de borrar |
| `monitores/lista.html` | Listado de monitores |
| `monitores/detalle.html` | Perfil del monitor con sus actividades |
| `monitores/form.html` | Formulario crear/editar monitor |
| `monitores/confirmar_eliminar.html` | Confirmación antes de borrar |
| `salas/lista.html` | Listado de salas |
| `salas/detalle.html` | Ficha de sala con actividades asignadas |
| `salas/form.html` | Formulario crear/editar sala |
| `salas/confirmar_eliminar.html` | Confirmación antes de borrar |

El diseño visual utiliza **Tailwind CSS via CDN**: tarjetas con sombra, gradiente en el navbar, badges de rol, y estilos de botón diferenciados por acción (primario/peligro/neutro).

---

## Instalación y puesta en marcha

### Requisitos

- Python 3.10 o superior
- pip

### Pasos

```bash
# 1. Clonar el repositorio
git clone <url-del-repositorio>
cd Practica_Final_Django

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate        # Linux/macOS
# venv\Scripts\activate         # Windows

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Aplicar migraciones
python manage.py migrate

# 5. (Opcional) Crear superusuario administrador
python manage.py createsuperuser

# 6. Arrancar el servidor de desarrollo
python manage.py runserver
```

La aplicación estará disponible en **http://127.0.0.1:8000/**.

### Usuarios de demo

Para probar los distintos roles sin necesidad de crear datos manualmente:

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `admin123` | Personal Administrativo |
| `monitor1` | `monitor123` | Monitor |
| `responsable1` | `responsable123` | Responsable de Sala |
| `usuario1` | `usuario123` | Usuario Inscrito |

---

## Tests

La suite de tests cubre modelos, señales, decoradores y todas las vistas:

```bash
python manage.py test gestion
```

```
Found 48 test(s).
OK
```

| Fichero de test | Cobertura |
|---|---|
| `test_models.py` | Creación y relaciones de modelos |
| `test_signals.py` | Incremento/decremento de plazas via Observer |
| `test_decorators.py` | Control de acceso por rol |
| `test_views_actividades.py` | CRUD de actividades y filtros GET |
| `test_views_inscripciones.py` | Inscripción, cancelación y plazas |
| `test_views_usuarios.py` | CRUD de usuarios y control de propiedad |
| `test_views_monitores.py` | CRUD de monitores y restricción de edición |
| `test_views_salas.py` | CRUD de salas y visibilidad por responsable |

---

## Estructura del proyecto

```
Practica_Final_Django/
├── manage.py
├── requirements.txt
├── MemoriaArquitecturaSoftware.pdf   ← Parte teórica (C4, Observer, MVC/MVT)
│
├── centro_cultural/                  ← Configuración del proyecto Django
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
└── gestion/                          ← App principal
    ├── models.py                     ← CustomUser, Sala, Actividad, Inscripcion
    ├── views.py                      ← 25 Function-Based Views
    ├── urls.py                       ← 25 URL patterns
    ├── forms.py                      ← ModelForms (5 formularios)
    ├── signals.py                    ← Patrón Observer
    ├── decorators.py                 ← @role_required
    ├── admin.py                      ← Registro en Django Admin
    ├── apps.py                       ← Conexión de señales en ready()
    ├── migrations/
    ├── tests/
    │   ├── test_models.py
    │   ├── test_signals.py
    │   ├── test_decorators.py
    │   ├── test_views_actividades.py
    │   ├── test_views_inscripciones.py
    │   ├── test_views_usuarios.py
    │   ├── test_views_monitores.py
    │   └── test_views_salas.py
    └── templates/
        ├── base.html
        ├── auth/
        ├── actividades/
        ├── inscripciones/
        ├── usuarios/
        ├── monitores/
        └── salas/
```
