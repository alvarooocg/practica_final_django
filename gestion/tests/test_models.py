from django.test import TestCase
from gestion.models import CustomUser


class CustomUserTest(TestCase):
    def test_create_usuario_with_rol(self):
        user = CustomUser.objects.create_user(
            username='usr1', password='pass123', rol='usuario',
            edad=25, telefono='600000000'
        )
        self.assertEqual(user.rol, 'usuario')
        self.assertEqual(user.edad, 25)
        self.assertEqual(user.telefono, '600000000')

    def test_create_monitor_with_especializacion(self):
        user = CustomUser.objects.create_user(
            username='mon1', password='pass123', rol='monitor',
            especializacion='Yoga'
        )
        self.assertEqual(user.rol, 'monitor')
        self.assertEqual(user.especializacion, 'Yoga')

    def test_default_rol_is_usuario(self):
        user = CustomUser.objects.create_user(username='u2', password='p')
        self.assertEqual(user.rol, 'usuario')


from django.utils import timezone
from gestion.models import CustomUser, Sala, Actividad, Inscripcion


class SalaTest(TestCase):
    def test_create_sala(self):
        responsable = CustomUser.objects.create_user(
            username='resp1', password='p', rol='responsable'
        )
        sala = Sala.objects.create(
            nombre='Sala A', capacidad=20, ubicacion='Planta 1',
            responsable=responsable
        )
        self.assertEqual(sala.nombre, 'Sala A')
        self.assertEqual(sala.responsable, responsable)

    def test_sala_sin_responsable(self):
        sala = Sala.objects.create(nombre='Sala B', capacidad=10, ubicacion='Planta 2')
        self.assertIsNone(sala.responsable)


class ActividadTest(TestCase):
    def setUp(self):
        self.monitor = CustomUser.objects.create_user(
            username='mon2', password='p', rol='monitor'
        )
        self.sala = Sala.objects.create(nombre='S1', capacidad=15, ubicacion='P1')

    def test_create_actividad(self):
        act = Actividad.objects.create(
            nombre='Pilates', tipo='deporte', horario=timezone.now(),
            descripcion='desc', duracion=60, plazas_disponibles=10,
            monitor=self.monitor, sala_principal=self.sala
        )
        self.assertEqual(act.nombre, 'Pilates')
        self.assertEqual(act.monitor, self.monitor)

    def test_actividad_salas_secundarias(self):
        sala2 = Sala.objects.create(nombre='S2', capacidad=10, ubicacion='P2')
        act = Actividad.objects.create(
            nombre='Danza', tipo='arte', horario=timezone.now(),
            descripcion='d', duracion=45, plazas_disponibles=5,
            monitor=self.monitor
        )
        act.salas_secundarias.add(sala2)
        self.assertIn(sala2, act.salas_secundarias.all())


class InscripcionTest(TestCase):
    def setUp(self):
        self.monitor = CustomUser.objects.create_user(username='m3', password='p', rol='monitor')
        self.usuario = CustomUser.objects.create_user(username='u3', password='p', rol='usuario')
        self.actividad = Actividad.objects.create(
            nombre='Yoga', tipo='deporte', horario=timezone.now(),
            descripcion='d', duracion=60, plazas_disponibles=5,
            monitor=self.monitor
        )

    def test_create_inscripcion(self):
        ins = Inscripcion.objects.create(usuario=self.usuario, actividad=self.actividad)
        self.assertEqual(ins.usuario, self.usuario)
        self.assertEqual(ins.actividad, self.actividad)

    def test_inscripcion_unique_together(self):
        Inscripcion.objects.create(usuario=self.usuario, actividad=self.actividad)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            Inscripcion.objects.create(usuario=self.usuario, actividad=self.actividad)
