from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse

from apps.absences.forms import CongeForm
from apps.absences.models import Conge
from apps.agents.models import Agent
from apps.enseignants.models import Etablissement, Professeur


User = get_user_model()


class CongeFormTests(TestCase):
	def setUp(self):
		self.agent = Agent.objects.create(
			matricule='AG001',
			nom='Diallo',
			prenom='Aminata',
			telephone='620000001',
			email='aminata.agent@example.com',
			fonction='Gestionnaire'
		)
		self.etablissement = Etablissement.objects.create(nom='ENI Test', code='ENI001')
		self.professeur = Professeur.objects.create(
			matricule='PR001',
			nom='Barry',
			prenom='Mamadou',
			email='mamadou.prof@example.com',
			telephone='620000002',
			specialite='Mathématiques',
			etablissement=self.etablissement
		)

	def test_form_peut_creer_un_conge_pour_un_agent(self):
		form = CongeForm(data={
			'agent': f'agent:{self.agent.pk}',
			'date_debut': date(2026, 4, 1),
			'date_fin': date(2026, 4, 5),
			'type_conge': 'annuel',
			'motif': 'Repos',
		})

		self.assertTrue(form.is_valid(), form.errors)
		conge = form.save()

		self.assertEqual(conge.agent, self.agent)
		self.assertIsNone(conge.professeur)

	def test_form_peut_creer_un_conge_pour_un_professeur(self):
		form = CongeForm(data={
			'agent': f'professeur:{self.professeur.pk}',
			'date_debut': date(2026, 4, 10),
			'date_fin': date(2026, 4, 12),
			'type_conge': 'maladie',
			'motif': 'Repos médical',
		})

		self.assertTrue(form.is_valid(), form.errors)
		conge = form.save()

		self.assertEqual(conge.professeur, self.professeur)
		self.assertIsNone(conge.agent)

	def test_form_refuse_un_chevauchement_pour_le_meme_beneficiaire(self):
		Conge.objects.create(
			agent=self.agent,
			user_demandeur=None,
			type_conge='annuel',
			date_debut=date(2026, 4, 1),
			date_fin=date(2026, 4, 5),
			motif='Premier congé',
			statut='demande',
		)

		form = CongeForm(data={
			'agent': f'agent:{self.agent.pk}',
			'date_debut': date(2026, 4, 4),
			'date_fin': date(2026, 4, 8),
			'type_conge': 'permission',
			'motif': 'Deuxième demande',
		})

		self.assertFalse(form.is_valid())
		self.assertIn('chevauche', str(form.non_field_errors()))


class CongeListViewTests(TestCase):
	def setUp(self):
		self.etablissement = Etablissement.objects.create(nom='ENI Direction', code='ENI-DIR', directeur='Alpha Diallo')
		self.autre_etablissement = Etablissement.objects.create(nom='ENI Autre', code='ENI-AUT')

		self.agent = Agent.objects.create(
			matricule='AG100',
			nom='Camara',
			prenom='Moussa',
			telephone='620000100',
			email='moussa.camara@example.com',
			fonction='Comptable'
		)
		self.autre_agent = Agent.objects.create(
			matricule='AG101',
			nom='Bah',
			prenom='Fatou',
			telephone='620000101',
			email='fatou.bah@example.com',
			fonction='Assistante'
		)

		self.directeur = User.objects.create_user(
			username='directeur',
			password='test12345',
			first_name='Alpha',
			last_name='Diallo',
			role='directeur_ecole',
		)
		self.directeur.user_permissions.add(
			Permission.objects.get(codename='approuver_conge_directeur')
		)

		self.conge_propre = Conge.objects.create(
			agent=self.agent,
			user_demandeur=self.directeur,
			type_conge='annuel',
			date_debut=date(2026, 4, 20),
			date_fin=date(2026, 4, 22),
			motif='Mon congé',
			statut='approuve_directeur',
			etablissement=self.autre_etablissement,
		)
		self.conge_a_traiter = Conge.objects.create(
			agent=self.autre_agent,
			type_conge='permission',
			date_debut=date(2026, 4, 10),
			date_fin=date(2026, 4, 10),
			motif='Besoin urgent',
			statut='demande',
			etablissement=self.etablissement,
		)
		self.conge_hors_scope = Conge.objects.create(
			agent=self.autre_agent,
			type_conge='maladie',
			date_debut=date(2026, 4, 11),
			date_fin=date(2026, 4, 12),
			motif='Hors périmètre',
			statut='demande',
			etablissement=self.autre_etablissement,
		)

	def test_liste_directeur_affiche_ses_demandes_et_son_perimetre(self):
		self.client.force_login(self.directeur)

		response = self.client.get(reverse('conge-list'))

		self.assertEqual(response.status_code, 200)
		conges = list(response.context['conges'])
		self.assertIn(self.conge_propre, conges)
		self.assertIn(self.conge_a_traiter, conges)
		self.assertNotIn(self.conge_hors_scope, conges)

	def test_filtre_statut_reste_applique_dans_le_perimetre_autorise(self):
		self.client.force_login(self.directeur)

		response = self.client.get(reverse('conge-list'), {'statut': 'demande'})

		self.assertEqual(response.status_code, 200)
		conges = list(response.context['conges'])
		self.assertIn(self.conge_a_traiter, conges)
		self.assertNotIn(self.conge_propre, conges)
		self.assertNotIn(self.conge_hors_scope, conges)
