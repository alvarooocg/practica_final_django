from django.test import TestCase
from django.urls import reverse
from gestion.models import CustomUser, Sala


class SalasViewTest(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='adm_s', password='pass', rol='admin')
        self.responsable = CustomUser.objects.create_user(username='resp_s', password='pass', rol='responsable')
        self.sala = Sala.objects.create(
            nombre='Sala Azul', capacidad=20, ubicacion='Planta 1',
            responsable=self.responsable
        )

    def test_lista_admin_ve_todas(self):
        self.client.login(username='adm_s', password='pass')
        response = self.client.get(reverse('salas_lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sala Azul')

    def test_lista_responsable_ve_sus_salas(self):
        self.client.login(username='resp_s', password='pass')
        response = self.client.get(reverse('salas_lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Sala Azul')

    def test_lista_usuario_denegado(self):
        usr = CustomUser.objects.create_user(username='usr_s', password='pass', rol='usuario')
        self.client.login(username='usr_s', password='pass')
        response = self.client.get(reverse('salas_lista'))
        self.assertEqual(response.status_code, 403)

    def test_crear_sala(self):
        self.client.login(username='adm_s', password='pass')
        response = self.client.post(reverse('sala_crear'), {
            'nombre': 'Sala Verde', 'capacidad': 15,
            'ubicacion': 'Planta 2', 'responsable': '',
        })
        self.assertRedirects(response, reverse('salas_lista'))
        self.assertTrue(Sala.objects.filter(nombre='Sala Verde').exists())

    def test_eliminar_sala(self):
        self.client.login(username='adm_s', password='pass')
        sid = self.sala.pk
        response = self.client.post(reverse('sala_eliminar', args=[sid]))
        self.assertRedirects(response, reverse('salas_lista'))
        self.assertFalse(Sala.objects.filter(pk=sid).exists())

    def test_responsable_no_puede_ver_sala_ajena(self):
        otra_sala = Sala.objects.create(nombre='Sala Roja', capacidad=10, ubicacion='P3')
        self.client.login(username='resp_s', password='pass')
        response = self.client.get(reverse('sala_detalle', args=[otra_sala.pk]))
        self.assertEqual(response.status_code, 403)
