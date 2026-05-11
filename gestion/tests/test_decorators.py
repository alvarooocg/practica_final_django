from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from django.core.exceptions import PermissionDenied
from gestion.models import CustomUser
from gestion.decorators import role_required


def dummy_view(request, *args, **kwargs):
    return HttpResponse('ok')


class RoleRequiredTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = CustomUser.objects.create_user(
            username='adm', password='p', rol='admin'
        )
        self.usuario = CustomUser.objects.create_user(
            username='usr', password='p', rol='usuario'
        )

    def test_allowed_role_gets_through(self):
        protected = role_required('admin')(dummy_view)
        request = self.factory.get('/')
        request.user = self.admin
        response = protected(request)
        self.assertEqual(response.status_code, 200)

    def test_wrong_role_raises_permission_denied(self):
        protected = role_required('admin')(dummy_view)
        request = self.factory.get('/')
        request.user = self.usuario
        with self.assertRaises(PermissionDenied):
            protected(request)

    def test_multiple_roles_allowed(self):
        protected = role_required('admin', 'monitor')(dummy_view)
        monitor = CustomUser.objects.create_user(username='mon', password='p', rol='monitor')
        request = self.factory.get('/')
        request.user = monitor
        response = protected(request)
        self.assertEqual(response.status_code, 200)
