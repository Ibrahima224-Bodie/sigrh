from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from .models import User


class PermissionAdministrationAccessTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='perm_reader',
			password='secret123',
			role='professeur',
		)

	def test_permission_list_access_with_view_permission(self):
		permission = Permission.objects.get(codename='view_permission', content_type__app_label='auth')
		self.user.user_permissions.add(permission)
		self.client.force_login(self.user)

		response = self.client.get(reverse('permission-list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Liste des permissions')

	def test_role_list_access_with_view_group_permission(self):
		permission = Permission.objects.get(codename='view_group', content_type__app_label='auth')
		self.user.user_permissions.add(permission)
		self.client.force_login(self.user)

		response = self.client.get(reverse('role-list'))

		self.assertEqual(response.status_code, 200)
		self.assertContains(response, 'Rôles')
