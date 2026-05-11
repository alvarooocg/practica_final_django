from django.test import TestCase
from django.urls import reverse
from gestion.models import CustomUser


class UsuariosViewTest(TestCase):
    def setUp(self):
        self.admin = CustomUser.objects.create_user(username='adm_u', password='pass', rol='admin')
        self.usuario = CustomUser.objects.create_user(
            username='usr_u', password='pass', rol='usuario', edad=30
        )

    def test_lista_solo_admin(self):
        self.client.login(username='usr_u', password='pass')
        response = self.client.get(reverse('usuarios_lista'))
        self.assertEqual(response.status_code, 403)

    def test_lista_ok_admin(self):
        self.client.login(username='adm_u', password='pass')
        response = self.client.get(reverse('usuarios_lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'usr_u')

    def test_detalle_propio_usuario(self):
        self.client.login(username='usr_u', password='pass')
        response = self.client.get(reverse('usuario_detalle', args=[self.usuario.pk]))
        self.assertEqual(response.status_code, 200)

    def test_detalle_ajeno_denegado(self):
        otro = CustomUser.objects.create_user(username='otro_u', password='pass', rol='usuario')
        self.client.login(username='usr_u', password='pass')
        response = self.client.get(reverse('usuario_detalle', args=[otro.pk]))
        self.assertEqual(response.status_code, 403)

    def test_crear_usuario(self):
        self.client.login(username='adm_u', password='pass')
        response = self.client.post(reverse('usuario_crear'), {
            'username': 'new_u', 'rol': 'usuario',
            'password1': 'segura1234', 'password2': 'segura1234',
        })
        self.assertRedirects(response, reverse('usuarios_lista'))
        self.assertTrue(CustomUser.objects.filter(username='new_u').exists())

    def test_eliminar_usuario(self):
        self.client.login(username='adm_u', password='pass')
        uid = self.usuario.pk
        response = self.client.post(reverse('usuario_eliminar', args=[uid]))
        self.assertRedirects(response, reverse('usuarios_lista'))
        self.assertFalse(CustomUser.objects.filter(pk=uid).exists())
