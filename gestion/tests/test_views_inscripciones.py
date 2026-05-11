from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from gestion.models import CustomUser, Actividad, Inscripcion


class InscripcionesViewTest(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='adm_i', password='pass', rol='admin')
        self.usuario = CustomUser.objects.create_user(username='usr_i', password='pass', rol='usuario')
        self.monitor = CustomUser.objects.create_user(username='mon_i', password='pass', rol='monitor')
        self.actividad = Actividad.objects.create(
            nombre='Salsa', tipo='danza', horario=timezone.now(),
            descripcion='d', duracion=60, plazas_disponibles=5,
            monitor=self.monitor
        )

    def test_inscribir_usuario(self):
        self.client.login(username='usr_i', password='pass')
        response = self.client.post(reverse('inscribir_usuario', args=[self.actividad.pk]))
        self.assertRedirects(response, reverse('actividad_detalle', args=[self.actividad.pk]))
        self.assertTrue(Inscripcion.objects.filter(usuario=self.usuario, actividad=self.actividad).exists())

    def test_inscribir_decrementa_plazas(self):
        self.client.login(username='usr_i', password='pass')
        self.client.post(reverse('inscribir_usuario', args=[self.actividad.pk]))
        self.actividad.refresh_from_db()
        self.assertEqual(self.actividad.plazas_disponibles, 4)

    def test_cancelar_propia_inscripcion(self):
        Inscripcion.objects.create(usuario=self.usuario, actividad=self.actividad)
        self.client.login(username='usr_i', password='pass')
        response = self.client.post(
            reverse('cancelar_inscripcion', args=[self.actividad.pk, self.usuario.pk])
        )
        self.assertRedirects(response, reverse('actividad_detalle', args=[self.actividad.pk]))
        self.assertFalse(Inscripcion.objects.filter(usuario=self.usuario, actividad=self.actividad).exists())

    def test_usuario_no_puede_cancelar_ajena(self):
        otro = CustomUser.objects.create_user(username='otro_i', password='pass', rol='usuario')
        Inscripcion.objects.create(usuario=otro, actividad=self.actividad)
        self.client.login(username='usr_i', password='pass')
        response = self.client.post(
            reverse('cancelar_inscripcion', args=[self.actividad.pk, otro.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_lista_inscripciones_admin(self):
        Inscripcion.objects.create(usuario=self.usuario, actividad=self.actividad)
        self.client.login(username='adm_i', password='pass')
        response = self.client.get(reverse('inscripciones_lista', args=[self.actividad.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'usr_i')

    def test_lista_inscripciones_monitor_propio(self):
        self.client.login(username='mon_i', password='pass')
        response = self.client.get(reverse('inscripciones_lista', args=[self.actividad.pk]))
        self.assertEqual(response.status_code, 200)

    def test_monitor_no_puede_ver_inscripciones_ajenas(self):
        otro_monitor = CustomUser.objects.create_user(username='mon2_i', password='pass', rol='monitor')
        self.client.login(username='mon2_i', password='pass')
        response = self.client.get(reverse('inscripciones_lista', args=[self.actividad.pk]))
        self.assertEqual(response.status_code, 403)
