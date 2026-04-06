from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.agents.models import Agent
from apps.comptes.models import User


class DashboardPermissionFilteringTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='prof_test',
			password='secret123',
			role='professeur',
		)
		self.dashboard_permission = Permission.objects.get(codename='access_dashboard', content_type__app_label='dashboard')
		self.chatbot_permission = Permission.objects.get(codename='use_ai_assistant', content_type__app_label='assistant_ia')
		self.dashboard_section_permissions = list(
			Permission.objects.filter(
				content_type__app_label='dashboard',
				codename__in=[
					'view_dashboard_agents_section',
					'view_dashboard_formations_section',
					'view_dashboard_professeurs_section',
					'view_dashboard_filieres_section',
					'view_dashboard_programmes_section',
					'view_dashboard_modules_section',
					'view_dashboard_etablissements_section',
					'view_dashboard_conges_section',
					'view_dashboard_carrieres_section',
				],
			)
		)
		self.user.user_permissions.add(self.dashboard_permission, self.chatbot_permission, *self.dashboard_section_permissions)
		Agent.objects.create(
			matricule='AG001',
			nom='Diallo',
			prenom='Mamadou',
			telephone='620000001',
			email='diallo.agent@example.com',
			fonction='Gestionnaire',
		)

	def test_dashboard_hides_agent_data_without_permission(self):
		agents_section_permission = Permission.objects.get(
			codename='view_dashboard_agents_section',
			content_type__app_label='dashboard',
		)
		self.user.user_permissions.remove(agents_section_permission)
		self.client.force_login(self.user)

		response = self.client.get(reverse('dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.context['can_view_agents'])
		self.assertNotContains(response, 'Agents Récents')
		self.assertNotContains(response, 'AG001')
		self.assertIsNone(response.context['total_agents'])

	def test_dashboard_shows_agent_data_with_permission(self):
		self.client.force_login(self.user)

		response = self.client.get(reverse('dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.context['can_view_agents'])
		self.assertContains(response, 'Agents Récents')
		self.assertContains(response, 'AG001')
		self.assertEqual(response.context['total_agents'], 1)

	def test_dashboard_redirects_without_dashboard_access_permission(self):
		self.user.user_permissions.remove(self.dashboard_permission)
		self.client.force_login(self.user)

		response = self.client.get(reverse('dashboard'), follow=True)

		self.assertRedirects(response, reverse('profile'))

	def test_chatbot_requires_dashboard_chatbot_permission(self):
		self.user.user_permissions.remove(self.chatbot_permission)
		self.client.force_login(self.user)

		response = self.client.post(
			reverse('chatbot-query'),
			data='{"question": "bonjour"}',
			content_type='application/json',
		)

		self.assertEqual(response.status_code, 403)

	def test_dashboard_without_agents_section_permission_hides_agent_blocks(self):
		agents_section_permission = Permission.objects.get(
			codename='view_dashboard_agents_section',
			content_type__app_label='dashboard',
		)
		self.user.user_permissions.remove(agents_section_permission)
		self.client.force_login(self.user)

		response = self.client.get(reverse('dashboard'))

		self.assertEqual(response.status_code, 200)
		self.assertFalse(response.context['can_view_agents'])
		self.assertNotContains(response, 'Agents Récents')
