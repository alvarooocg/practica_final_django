from django.test import TestCase
from django.utils import timezone
from gestion.models import CustomUser, Actividad, Inscripcion


class SignalTest(TestCase):
    def setUp(self):
        self.monitor = CustomUser.objects.create_user(
            username='mon_s', password='p', rol='monitor'
        )
        self.actividad = Actividad.objects.create(
            nombre='Zumba', tipo='deporte', horario=timezone.now(),
            descripcion='d', duracion=60, plazas_disponibles=5,
            monitor=self.monitor
        )
        self.usuario = CustomUser.objects.create_user(
            username='usr_s', password='p', rol='usuario'
        )

    def test_inscripcion_decrementa_plazas(self):
        Inscripcion.objects.create(usuario=self.usuario, actividad=self.actividad)
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.plazas_disponibles, 4)

    def test_cancelar_inscripcion_incrementa_plazas(self):
        ins = Inscripcion.objects.create(usuario=self.usuario, actividad=self.actividad)
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.plazas_disponibles, 4)
        ins.delete()
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.plazas_disponibles, 5)

    def test_plazas_no_bajan_de_cero(self):
        self.actividad.plazas_disponibles = 0
        self.actividad.save()
        Inscripcion.objects.create(usuario=self.usuario, actividad=self.actividad)
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.plazas_disponibles, 0)
