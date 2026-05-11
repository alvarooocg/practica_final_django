from django.test import TestCase
from django.urls import reverse
from gestion.models import CustomUser


class MonitoresViewTest(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='adm_m', password='pass', rol='admin')
        self.monitor = CustomUser.objects.create_user(
            username='mon_m', password='pass', rol='monitor', especializacion='Natación'
        )

    def test_lista_monitor_puede_ver(self):
        self.client.login(username='mon_m', password='pass')
        response = self.client.get(reverse('monitores_lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'mon_m')

    def test_lista_usuario_denegado(self):
        usr = CustomUser.objects.create_user(username='usr_m', password='pass', rol='usuario')
        self.client.login(username='usr_m', password='pass')
        response = self.client.get(reverse('monitores_lista'))
        self.assertEqual(response.status_code, 403)

    def test_crear_monitor(self):
        self.client.login(username='adm_m', password='pass')
        response = self.client.post(reverse('monitor_crear'), {
            'username': 'new_mon', 'especializacion': 'Yoga',
            'password1': 'segura1234', 'password2': 'segura1234',
        })
        self.assertRedirects(response, reverse('monitores_lista'))
        self.assertTrue(CustomUser.objects.filter(username='new_mon', rol='monitor').exists())

    def test_eliminar_monitor(self):
        self.client.login(username='adm_m', password='pass')
        mid = self.monitor.pk
        response = self.client.post(reverse('monitor_eliminar', args=[mid]))
        self.assertRedirects(response, reverse('monitores_lista'))
        self.assertFalse(CustomUser.objects.filter(pk=mid).exists())

    def test_monitor_edita_solo_su_perfil(self):
        otro = CustomUser.objects.create_user(username='mon2_m', password='pass', rol='monitor')
        self.client.login(username='mon_m', password='pass')
        response = self.client.get(reverse('monitor_editar', args=[otro.pk]))
        self.assertEqual(response.status_code, 403)
