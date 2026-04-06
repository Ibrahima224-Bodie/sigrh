from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from apps.enseignants.models import Affectation, Etablissement, Filiere, Module, Professeur, Programme
from apps.enseignants.forms import AffectationForm, ProfesseurForm


User = get_user_model()


class AffectationHeuresTests(TestCase):
    def setUp(self):
        self.etablissement = Etablissement.objects.create(nom='ERAM DE LABE', code='ERAMLABE')
        self.autre_etablissement = Etablissement.objects.create(nom='CFP MAMOU', code='CFPMAMOU')

        self.module_soudure = Module.objects.create(
            nom='Assemblage thermique et soudure',
            code='MOD-SOUD',
            nombre_heures=155,
            ordre=1,
        )
        self.module_meca = Module.objects.create(
            nom='Maintenance moteur diesel',
            code='MOD-DIESEL',
            nombre_heures=75,
            ordre=2,
        )

        self.filiere_labe = Filiere.objects.create(
            nom='Maintenance véhicules légers',
            code='MVL-LABE',
            etablissement=self.etablissement,
            duree_mois=12,
            nombre_heures_total=230,
        )
        self.filiere_mamou = Filiere.objects.create(
            nom='Maintenance engins',
            code='ME-MAMOU',
            etablissement=self.autre_etablissement,
            duree_mois=12,
            nombre_heures_total=180,
        )

        self.programme_labe = Programme.objects.create(
            nom='Mécanique',
            code='PROG-MECA-L',
            filiere=self.filiere_labe,
            semestre=1,
            nombre_heures=155,
            ordre=1,
        )
        self.programme_labe.module_formation.add(self.module_soudure)

        self.programme_mamou = Programme.objects.create(
            nom='Diesel',
            code='PROG-DIES-M',
            filiere=self.filiere_mamou,
            semestre=1,
            nombre_heures=75,
            ordre=1,
        )
        self.programme_mamou.module_formation.add(self.module_meca)

        self.prof_1 = Professeur.objects.create(
            matricule='P001',
            nom='Diallo',
            prenom='Alpha',
            specialite='Mécanique générale',
            etablissement=self.etablissement,
            heures_affectees=230,
            heures_disponibles=230,
        )
        self.prof_2 = Professeur.objects.create(
            matricule='P002',
            nom='Barry',
            prenom='Binta',
            specialite='Soudure',
            etablissement=self.etablissement,
            heures_affectees=160,
            heures_disponibles=160,
        )
        self.user = User.objects.create_user(username='gestionnaire-tests', password='test12345', is_staff=True, is_superuser=True)

    def test_un_module_peut_etre_partage_entre_plusieurs_professeurs(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=95,
            date_debut=date(2026, 4, 1),
        )

        seconde_affectation = Affectation(
            professeur=self.prof_2,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=60,
            date_debut=date(2026, 4, 2),
        )

        seconde_affectation.full_clean()
        seconde_affectation.save()

        self.assertEqual(Affectation.objects.filter(module=self.module_soudure, etablissement=self.etablissement).count(), 2)

    def test_affectation_refusee_si_heures_module_depassees(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=95,
            date_debut=date(2026, 4, 1),
        )

        affectation = Affectation(
            professeur=self.prof_2,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=70,
            date_debut=date(2026, 4, 2),
        )

        with self.assertRaises(ValidationError):
            affectation.full_clean()

    def test_un_professeur_peut_etre_reaffecte_dans_une_autre_ecole_s_il_a_des_heures_restantes(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=155,
            date_debut=date(2026, 4, 1),
            date_fin=date(2026, 4, 9),
        )

        affectation = Affectation(
            professeur=self.prof_1,
            module=self.module_meca,
            etablissement=self.autre_etablissement,
            filiere=self.filiere_mamou,
            nombre_heures=75,
            heures_affectees=75,
            date_debut=date(2026, 4, 10),
        )

        affectation.full_clean()
        affectation.save()
        self.prof_1.refresh_from_db()

        self.assertEqual(self.prof_1.heures_affectees, 230)
        self.assertEqual(self.prof_1.heures_restantes, 0)

    def test_vue_besoins_signale_partiel_si_toutes_les_heures_ne_sont_pas_couvertes(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=95,
            date_debut=date(2026, 4, 1),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('enseignants:besoin_list'))

        self.assertEqual(response.status_code, 200)
        row = next(item for item in response.context['besoin_rows'] if item['module'].pk == self.module_soudure.pk)
        self.assertEqual(row['etat'], 'PARTIEL')
        self.assertEqual(row['existant'], 95)
        self.assertEqual(row['besoins'], 60)

    def test_api_apercu_affectation_retourne_les_restes_utiles(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=95,
            date_debut=date(2026, 4, 1),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('enseignants:ajax-affectation-preview'), {
            'professeur_id': self.prof_2.pk,
            'module_id': self.module_soudure.pk,
            'etablissement_id': self.etablissement.pk,
            'filiere_id': self.filiere_labe.pk,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['besoin']['heures_restantes'], 60)
        self.assertEqual(payload['professeur']['heures_restantes'], 160)
        self.assertEqual(payload['heures_suggerees'], 60)

    def test_vue_suggestions_propose_un_professeur_et_prefill_affectation(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=95,
            date_debut=date(2026, 4, 1),
        )

        self.client.force_login(self.user)
        response = self.client.get(
            reverse('enseignants:besoin_suggestions', kwargs={'module_id': self.module_soudure.pk}),
            {'etablissement': self.etablissement.pk, 'filiere': self.filiere_labe.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['besoin_row']['besoins'], 60)
        self.assertTrue(response.context['suggestions'])
        top_suggestion = response.context['suggestions'][0]
        self.assertEqual(top_suggestion['professeur'].pk, self.prof_2.pk)
        self.assertEqual(top_suggestion['heures_proposees'], 60)
        self.assertIn(f'professeur={self.prof_2.pk}', top_suggestion['create_affectation_url'])

    def test_formulaire_affectation_est_prefille_depuis_les_suggestions(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('enseignants:affectation_create'), {
            'professeur': self.prof_2.pk,
            'etablissement': self.etablissement.pk,
            'filiere': self.filiere_labe.pk,
            'module': self.module_soudure.pk,
            'heures_affectees': 60,
        })

        self.assertEqual(response.status_code, 200)
        form = response.context['form']
        self.assertEqual(str(form['professeur'].value()), str(self.prof_2.pk))
        self.assertEqual(str(form['etablissement'].value()), str(self.etablissement.pk))
        self.assertEqual(str(form['filiere'].value()), str(self.filiere_labe.pk))
        self.assertEqual(str(form['module'].value()), str(self.module_soudure.pk))
        self.assertEqual(str(form['heures_affectees'].value()), '60')

    def test_formulaire_refuse_depassement_heures_restantes_professeur(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=150,
            date_debut=date(2026, 4, 1),
        )

        form = AffectationForm(data={
            'professeur': self.prof_1.pk,
            'etablissement': self.etablissement.pk,
            'filiere': self.filiere_labe.pk,
            'module': self.module_meca.pk,
            'heures_affectees': 90,
            'priorite': '2',
            'date_debut': '2026-04-02',
            'date_fin': '',
            'observations': '',
            'actif': 'on',
        })

        self.assertFalse(form.is_valid())
        self.assertIn('heures_affectees', form.errors)
        self.assertIn('80h restantes', str(form.errors['heures_affectees']))

    def test_api_apercu_retourne_max_heures_affectables(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=95,
            date_debut=date(2026, 4, 1),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('enseignants:ajax-affectation-preview'), {
            'professeur_id': self.prof_1.pk,
            'module_id': self.module_soudure.pk,
            'etablissement_id': self.etablissement.pk,
            'filiere_id': self.filiere_labe.pk,
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload['max_heures_professeur'], 135)
        self.assertEqual(payload['max_heures_besoin'], 60)
        self.assertEqual(payload['max_heures_affectables'], 60)

    def test_api_filieres_garde_la_filiere_courante_en_update(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('enseignants:ajax-filieres-by-etablissement'), {
            'etablissement_id': self.autre_etablissement.pk,
            'include_filiere_id': self.filiere_labe.pk,
        })

        self.assertEqual(response.status_code, 200)
        result_ids = {item['id'] for item in response.json().get('results', [])}
        self.assertIn(self.filiere_labe.pk, result_ids)

    def test_api_modules_garde_le_module_courant_en_update(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('enseignants:ajax-modules-by-filiere'), {
            'filiere_id': self.filiere_mamou.pk,
            'include_module_id': self.module_soudure.pk,
        })

        self.assertEqual(response.status_code, 200)
        result_ids = {item['id'] for item in response.json().get('results', [])}
        self.assertIn(self.module_soudure.pk, result_ids)

    def test_formulaire_update_precharge_les_dates_existantes(self):
        affectation = Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=60,
            date_debut=date(2026, 4, 1),
            date_fin=date(2026, 4, 30),
        )

        form = AffectationForm(instance=affectation)
        self.assertEqual(str(form['date_debut'].value()), '2026-04-01')
        self.assertEqual(str(form['date_fin'].value()), '2026-04-30')

    def test_refuse_affectation_si_professeur_deja_occupe_sur_la_periode(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=60,
            date_debut=date(2026, 4, 1),
            date_fin=date(2026, 4, 30),
        )

        affectation = Affectation(
            professeur=self.prof_1,
            module=self.module_meca,
            etablissement=self.autre_etablissement,
            filiere=self.filiere_mamou,
            nombre_heures=75,
            heures_affectees=30,
            date_debut=date(2026, 4, 15),
            date_fin=date(2026, 5, 10),
        )

        with self.assertRaises(ValidationError):
            affectation.full_clean()

    def test_autorise_autre_prof_sur_module_en_cours_de_couverture(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=95,
            date_debut=date(2026, 4, 1),
            date_fin=date(2026, 4, 30),
        )

        affectation = Affectation(
            professeur=self.prof_2,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=60,
            date_debut=date(2026, 4, 10),
            date_fin=date(2026, 4, 30),
        )
        affectation.full_clean()
        affectation.save()

        self.assertEqual(Affectation.objects.filter(module=self.module_soudure, etablissement=self.etablissement).count(), 2)

    def test_api_apercu_signale_professeur_occupe(self):
        Affectation.objects.create(
            professeur=self.prof_1,
            module=self.module_soudure,
            etablissement=self.etablissement,
            filiere=self.filiere_labe,
            nombre_heures=155,
            heures_affectees=60,
            date_debut=date(2026, 4, 1),
            date_fin=date(2026, 4, 30),
        )

        self.client.force_login(self.user)
        response = self.client.get(reverse('enseignants:ajax-affectation-preview'), {
            'professeur_id': self.prof_1.pk,
            'module_id': self.module_meca.pk,
            'etablissement_id': self.autre_etablissement.pk,
            'filiere_id': self.filiere_mamou.pk,
            'date_debut': '2026-04-15',
            'date_fin': '2026-04-20',
        })

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['professeur_occupe'])
        self.assertEqual(payload['max_heures_affectables'], 0)


class ProfesseurHeuresFormTests(TestCase):
    def setUp(self):
        self.etablissement = Etablissement.objects.create(nom='ERAM DE KINDIA', code='ERAMKINDIA')
        self.module = Module.objects.create(
            nom='Electricite industrielle',
            code='MOD-ELEC',
            nombre_heures=120,
            ordre=1,
        )
        self.filiere = Filiere.objects.create(
            nom='Electromecanique',
            code='ELM-KND',
            etablissement=self.etablissement,
            duree_mois=12,
            nombre_heures_total=180,
        )
        self.programme = Programme.objects.create(
            nom='Programme Electromecanique',
            code='PROG-ELM',
            filiere=self.filiere,
            semestre=1,
            nombre_heures=120,
            ordre=1,
        )
        self.programme.module_formation.add(self.module)
        self.professeur = Professeur.objects.create(
            matricule='P100',
            nom='Camara',
            prenom='Moussa',
            specialite='Electricite',
            etablissement=self.etablissement,
            heures_affectees=160,
            heures_disponibles=160,
        )
        Affectation.objects.create(
            professeur=self.professeur,
            module=self.module,
            etablissement=self.etablissement,
            filiere=self.filiere,
            nombre_heures=120,
            heures_affectees=90,
            date_debut=date(2026, 4, 1),
        )
        self.professeur.refresh_heures_depuis_affectations()

    def test_formulaire_professeur_charge_les_heures_affectees_instance(self):
        form = ProfesseurForm(instance=self.professeur)

        self.assertEqual(form.fields['heures_affectees'].initial, 160)
        self.assertNotIn('heures_disponibles', form.fields)

    def test_formulaire_professeur_permet_modifier_heures_affectees(self):
        form = ProfesseurForm(
            data={
                'matricule': self.professeur.matricule,
                'prenom': self.professeur.prenom,
                'nom': self.professeur.nom,
                'sexe': self.professeur.sexe,
                'hierarchie': self.professeur.hierarchie,
                'specialite': self.professeur.specialite,
                'statut': self.professeur.statut,
                'corps': self.professeur.corps,
                'email': self.professeur.email,
                'telephone': self.professeur.telephone,
                'heures_affectees': 110,
                'etablissement': self.etablissement.pk,
                'date_embauche': '',
                'actif': 'on',
            },
            instance=self.professeur,
        )

        self.assertTrue(form.is_valid(), form.errors)
        instance = form.save()
        self.assertEqual(instance.heures_affectees, 110)

    def test_heures_restantes_ne_deviennent_pas_negatives(self):
        self.professeur.heures_affectees = 50
        self.professeur.save(update_fields=['heures_affectees'])

        self.assertEqual(self.professeur.heures_restantes, 0)

    def test_heures_restantes_tiennent_compte_des_affectations_actives(self):
        self.professeur.heures_affectees = 120
        self.professeur.save(update_fields=['heures_affectees'])

        self.assertEqual(self.professeur.heures_restantes, 30)

    def test_taux_utilisation_base_sur_heures_affectees_et_restantes(self):
        self.professeur.heures_affectees = 120
        self.professeur.save(update_fields=['heures_affectees'])

        self.assertEqual(self.professeur.heures_restantes, 30)
        self.assertEqual(self.professeur.taux_utilisation, 75.0)

    def test_taux_utilisation_est_zero_sans_affectation_module(self):
        self.professeur.affectations.all().delete()
        self.professeur.heures_affectees = 438
        self.professeur.save(update_fields=['heures_affectees'])

        self.assertEqual(self.professeur.heures_affectees_modules, 0)
        self.assertEqual(self.professeur.heures_restantes, 438)
        self.assertEqual(self.professeur.taux_utilisation, 0)