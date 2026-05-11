from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from gestion.models import CustomUser, Sala, Actividad, Inscripcion


class ActividadesViewTest(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(
            username='adm_a', password='pass', rol='admin'
        )
        self.usuario = CustomUser.objects.create_user(
            username='usr_a', password='pass', rol='usuario'
        )
        self.monitor = CustomUser.objects.create_user(
            username='mon_a', password='pass', rol='monitor'
        )
        self.actividad = Actividad.objects.create(
            nombre='Yoga', tipo='deporte', horario=timezone.now(),
            descripcion='desc', duracion=60, plazas_disponibles=5,
            monitor=self.monitor
        )

    def test_lista_requiere_login(self):
        response = self.client.get(reverse('actividades_lista'))
        self.assertRedirects(response, '/login/?next=/actividades/')

    def test_lista_ok_para_admin(self):
        self.client.login(username='adm_a', password='pass')
        response = self.client.get(reverse('actividades_lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Yoga')

    def test_lista_filtro_tipo(self):
        self.client.login(username='adm_a', password='pass')
        response = self.client.get(reverse('actividades_lista') + '?tipo=deporte')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Yoga')

    def test_lista_filtro_tipo_sin_coincidencia(self):
        self.client.login(username='adm_a', password='pass')
        response = self.client.get(reverse('actividades_lista') + '?tipo=danza')
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Yoga')

    def test_detalle_ok(self):
        self.client.login(username='usr_a', password='pass')
        response = self.client.get(reverse('actividad_detalle', args=[self.actividad.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Yoga')

    def test_crear_solo_admin(self):
        self.client.login(username='usr_a', password='pass')
        response = self.client.get(reverse('actividad_crear'))
        self.assertEqual(response.status_code, 403)

    def test_crear_actividad_post(self):
        self.client.login(username='adm_a', password='pass')
        data = {
            'nombre': 'Pilates', 'tipo': 'deporte',
            'horario': '2026-06-01T10:00',
            'descripcion': 'clase', 'duracion': 45,
            'plazas_disponibles': 10, 'monitor': self.monitor.pk,
            'salas_secundarias': [],
        }
        response = self.client.post(reverse('actividad_crear'), data)
        self.assertRedirects(response, reverse('actividades_lista'))
        self.assertTrue(Actividad.objects.filter(nombre='Pilates').exists())

    def test_eliminar_solo_admin(self):
        self.client.login(username='mon_a', password='pass')
        response = self.client.post(
            reverse('actividad_eliminar', args=[self.actividad.pk])
        )
        self.assertEqual(response.status_code, 403)

    def test_eliminar_actividad(self):
        self.client.login(username='adm_a', password='pass')
        response = self.client.post(
            reverse('actividad_eliminar', args=[self.actividad.pk])
        )
        self.assertRedirects(response, reverse('actividades_lista'))
        self.assertFalse(Actividad.objects.filter(pk=self.actividad.pk).exists())
