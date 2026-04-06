from django import forms
from django.db.models import Q
from .models import (
    Etablissement,
    Filiere,
    Programme,
    Module,
    Professeur,
    Affectation,
    Region,
    Prefecture,
    Commune,
    Quartier,
    Secteur,
)


class RegionForm(forms.ModelForm):
    class Meta:
        model = Region
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la région'}),
        }


class PrefectureForm(forms.ModelForm):
    region = forms.ModelChoiceField(
        queryset=Region.objects.order_by('nom'),
        empty_label='Sélectionner une région',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Prefecture
        fields = ['region', 'nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la préfecture'}),
        }


class CommuneForm(forms.ModelForm):
    class Meta:
        model = Commune
        fields = ['prefecture', 'nom']
        widgets = {
            'prefecture': forms.Select(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la commune'}),
        }


class QuartierForm(forms.ModelForm):
    class Meta:
        model = Quartier
        fields = ['commune', 'nom']
        widgets = {
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du quartier/district'}),
        }


class SecteurForm(forms.ModelForm):
    commune = forms.ModelChoiceField(
        queryset=Commune.objects.order_by('nom'),
        required=True,
        empty_label='Sélectionner une commune',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    quartier = forms.ModelChoiceField(
        queryset=Quartier.objects.none(),
        required=True,
        empty_label='Sélectionner un quartier',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Le champ HTML date attend YYYY-MM-DD pour afficher les valeurs existantes.
        self.fields['date_debut'].input_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']
        self.fields['date_fin'].input_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']

        commune_id = self.data.get('commune')
        if commune_id:
            self.fields['quartier'].queryset = Quartier.objects.filter(commune_id=commune_id).order_by('nom')
        elif self.instance.pk and self.instance.quartier_id:
            commune = self.instance.quartier.commune
            self.fields['commune'].initial = commune
            self.fields['quartier'].queryset = Quartier.objects.filter(commune=commune).order_by('nom')
        else:
            self.fields['quartier'].queryset = Quartier.objects.none()

    def clean(self):
        cleaned = super().clean()
        commune = cleaned.get('commune')
        quartier = cleaned.get('quartier')
        if commune and quartier and quartier.commune_id != commune.id:
            self.add_error('quartier', 'Le quartier sélectionné ne correspond pas à la commune choisie.')
        return cleaned

    class Meta:
        model = Secteur
        fields = ['quartier', 'nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du secteur'}),
        }


class EtablissementForm(forms.ModelForm):
    code = forms.CharField(
        required=False,
        disabled=True,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'readonly': 'readonly',
                'placeholder': 'Généré automatiquement après enregistrement'
            }
        ),
        help_text='Code généré automatiquement: 3 lettres de la région + 3 lettres du nom de l\'école.'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance and self.instance.pk and self.instance.code:
            self.fields['code'].initial = self.instance.code

        self.fields['region'].queryset = Region.objects.order_by('nom')

        self.fields['prefecture'].queryset = Prefecture.objects.none()
        self.fields['commune'].queryset = Commune.objects.none()
        self.fields['quartier'].queryset = Quartier.objects.none()
        self.fields['secteur'].queryset = Secteur.objects.none()

        region_id = self.data.get('region') or getattr(self.instance, 'region_id', None)
        prefecture_id = self.data.get('prefecture') or getattr(self.instance, 'prefecture_id', None)
        commune_id = self.data.get('commune') or getattr(self.instance, 'commune_id', None)
        quartier_id = self.data.get('quartier') or getattr(self.instance, 'quartier_id', None)

        if region_id:
            self.fields['prefecture'].queryset = Prefecture.objects.filter(region_id=region_id).order_by('nom')

        if prefecture_id:
            self.fields['commune'].queryset = Commune.objects.filter(prefecture_id=prefecture_id).order_by('nom')

        if commune_id:
            self.fields['quartier'].queryset = Quartier.objects.filter(commune_id=commune_id).order_by('nom')

        if quartier_id:
            self.fields['secteur'].queryset = Secteur.objects.filter(quartier_id=quartier_id).order_by('nom')

    class Meta:
        model = Etablissement
        fields = [
            'nom', 'code', 'localisation', 'contact', 'email', 'directeur', 'date_creation',
            'region', 'prefecture', 'commune', 'quartier', 'secteur'
        ]
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de l\'établissement'}),
            'localisation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: 9.6412, -13.5784 (longitude, latitude)'}),
            'contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Contact'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'directeur': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Directeur'}),
            'date_creation': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'prefecture': forms.Select(attrs={'class': 'form-control'}),
            'commune': forms.Select(attrs={'class': 'form-control'}),
            'quartier': forms.Select(attrs={'class': 'form-control'}),
            'secteur': forms.Select(attrs={'class': 'form-control'}),
        }


class FiliereForm(forms.ModelForm):
    etablissements = forms.ModelMultipleChoiceField(
        queryset=Etablissement.objects.order_by('nom'),
        required=True,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '8'}),
        help_text='Sélectionnez un ou plusieurs établissements (Ctrl+clic pour une sélection multiple).'
    )
    programmes = forms.ModelMultipleChoiceField(
        queryset=Programme.objects.order_by('nom'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '8'}),
        help_text='Sélectionnez un ou plusieurs programmes (Ctrl+clic pour une sélection multiple).'
    )
    nombre_heures_total = forms.IntegerField(
        required=False,
        disabled=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        help_text="Calculé automatiquement selon les programmes sélectionnés."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            etablissement_ids = list(self.instance.etablissements.values_list('id', flat=True))
            if not etablissement_ids and self.instance.etablissement_id:
                etablissement_ids = [self.instance.etablissement_id]
            self.fields['etablissements'].initial = etablissement_ids
        if self.instance and self.instance.pk:
            selected_programmes = self.instance.programmes.all().order_by('nom')
            self.fields['programmes'].initial = selected_programmes
            self.fields['nombre_heures_total'].initial = self._calculate_nombre_heures_total(selected_programmes)

    @staticmethod
    def _calculate_nombre_heures_total(programmes):
        return sum(programme.nombre_heures or 0 for programme in programmes)

    def clean(self):
        cleaned_data = super().clean()
        programmes = cleaned_data.get('programmes')
        cleaned_data['nombre_heures_total'] = self._calculate_nombre_heures_total(programmes or [])
        return cleaned_data

    class Meta:
        model = Filiere
        fields = ['nom', 'code', 'description', 'duree_mois', 'nombre_heures_total']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la filière'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'duree_mois': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Durée en mois'}),
        }


class ProgrammeForm(forms.ModelForm):
    module_formation = forms.ModelMultipleChoiceField(
        queryset=Module.objects.order_by('nom'),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '8'}),
        help_text='Sélectionnez un ou plusieurs modules (Ctrl+clic pour une sélection multiple).'
    )
    nombre_heures = forms.IntegerField(
        required=False,
        disabled=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        help_text="Calculé automatiquement selon les modules sélectionnés."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['nombre_heures'].initial = self._calculate_nombre_heures(
                self.instance.module_formation.all()
            )

    @staticmethod
    def _calculate_nombre_heures(modules):
        return sum(module.nombre_heures or 0 for module in modules)

    def clean(self):
        cleaned_data = super().clean()
        modules = cleaned_data.get('module_formation')
        cleaned_data['nombre_heures'] = self._calculate_nombre_heures(modules or [])
        return cleaned_data

    class Meta:
        model = Programme
        fields = ['nom', 'code', 'description', 'module_formation', 'semestre', 'nombre_heures', 'ordre']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du programme'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'semestre': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Semestre'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ordre'}),
        }


class ModuleForm(forms.ModelForm):
    class Meta:
        model = Module
        fields = ['nom', 'code', 'description', 'nombre_heures', 'ordre']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du module'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
            'nombre_heures': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Nombre d\'heures'}),
            'ordre': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Ordre'}),
        }


class ProfesseurForm(forms.ModelForm):
    etablissement = forms.ModelChoiceField(
        queryset=Etablissement.objects.order_by('nom'),
        empty_label='Sélectionner un établissement',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.fields['etablissement'].queryset = Etablissement.objects.order_by('nom')
        self.heures_deja_affectees = self._get_heures_deja_affectees()

        # heures_affectees : champ modifiable par l'utilisateur
        self.fields['heures_affectees'].required = True
        self.fields['heures_affectees'].widget.attrs.update({
            'min': 0,
            'class': 'form-control',
        })

        # Le champ HTML date attend YYYY-MM-DD pour bien precharger la valeur existante.
        self.fields['date_embauche'].input_formats = ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']

        if not self.is_bound:
            if self.instance and self.instance.pk:
                self.fields['heures_affectees'].initial = self.instance.heures_affectees or 0
                if self.instance.date_embauche:
                    self.fields['date_embauche'].initial = self.instance.date_embauche.strftime('%Y-%m-%d')
            else:
                # En création, initialiser à 0
                self.fields['heures_affectees'].initial = 0

    def _get_heures_deja_affectees(self):
        if not self.instance or not self.instance.pk:
            return 0
        return sum(
            affectation.heures_affectees
            for affectation in self.instance.affectations.filter(actif=True)
        )

    def clean(self):
        cleaned_data = super().clean()
        heures_affectees = cleaned_data.get('heures_affectees')

        if heures_affectees is None:
            heures_affectees = self.instance.heures_affectees if self.instance and self.instance.pk else 0

        if heures_affectees < 0:
            self.add_error('heures_affectees', "Les heures affectées doivent être positives.")

        if heures_affectees < self.heures_deja_affectees:
            self.add_error(
                'heures_affectees',
                f"Les heures affectées ne peuvent pas être inférieures aux heures utilisées ({self.heures_deja_affectees}h)."
            )

        cleaned_data['heures_affectees'] = heures_affectees
        return cleaned_data

    def save(self, commit=True):
        professeur = super().save(commit=False)

        professeur.heures_affectees = self.cleaned_data.get('heures_affectees') or 0

        if commit:
            professeur.save()
        return professeur

    class Meta:
        model = Professeur
        fields = [
            'matricule', 'prenom', 'nom', 'sexe', 'hierarchie', 'specialite', 'statut', 'corps',
            'email', 'telephone', 'photo', 'heures_affectees', 'etablissement', 'date_embauche', 'actif'
        ]
        labels = {
            'heures_affectees': 'Heures affectées',
        }
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matricule'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'sexe': forms.Select(attrs={'class': 'form-control'}),
            'hierarchie': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hiérarchie'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'specialite': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Spécialité'}),
            'statut': forms.Select(attrs={'class': 'form-control'}),
            'corps': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Corps'}),
            'heures_affectees': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Heures affectées'}),
            'etablissement': forms.Select(attrs={'class': 'form-control'}),
            'date_embauche': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AffectationForm(forms.ModelForm):
    programme = forms.ModelChoiceField(
        queryset=Programme.objects.none(),
        required=False,
        empty_label='Sélectionner un programme',
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    nombre_heures = forms.IntegerField(
        required=False,
        disabled=True,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        help_text="Calculé automatiquement selon le module sélectionné."
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['filiere'].queryset = Filiere.objects.none()

        etablissement_id = (
            self.data.get('etablissement')
            or self.initial.get('etablissement')
            or getattr(self.instance, 'etablissement_id', None)
        )
        if etablissement_id:
            self.fields['filiere'].queryset = Filiere.objects.filter(
                Q(etablissements__id=etablissement_id) | Q(etablissement_id=etablissement_id)
            ).distinct().order_by('nom')
        elif self.instance and self.instance.pk and self.instance.filiere_id:
            self.fields['filiere'].queryset = Filiere.objects.filter(pk=self.instance.filiere_id)

        # En modification, garantir que la filiere existante reste selectionnable.
        if self.instance and self.instance.pk and self.instance.filiere_id:
            self.fields['filiere'].queryset = Filiere.objects.filter(
                Q(pk__in=self.fields['filiere'].queryset.values_list('pk', flat=True))
                | Q(pk=self.instance.filiere_id)
            ).distinct().order_by('nom')

        self.fields['module'].queryset = Module.objects.none()

        self.fields['programme'].queryset = Programme.objects.none()

        filiere_id = (
            self.data.get('filiere')
            or self.initial.get('filiere')
            or getattr(self.instance, 'filiere_id', None)
        )
        if filiere_id:
            self.fields['programme'].queryset = Programme.objects.filter(filiere_id=filiere_id).order_by('nom')

        programme_id = (
            self.data.get('programme')
            or self.initial.get('programme')
        )

        if not programme_id and self.instance and self.instance.pk and self.instance.module_id and filiere_id:
            programme = (
                self.instance.module.programmes_principaux.filter(filiere_id=filiere_id)
                .order_by('nom')
                .first()
            )
            if programme:
                programme_id = programme.pk
                self.fields['programme'].initial = programme.pk

        if programme_id and str(programme_id).isdigit():
            self.fields['module'].queryset = (
                Module.objects.filter(programmes_principaux__id=int(programme_id))
                .distinct()
                .order_by('nom')
            )
        if filiere_id:
            if not self.fields['module'].queryset.exists():
                self.fields['module'].queryset = (
                    Module.objects.filter(programmes_principaux__filiere_id=filiere_id)
                    .distinct()
                    .order_by('nom')
                )
        elif self.instance and self.instance.pk and self.instance.module_id:
            self.fields['module'].queryset = Module.objects.filter(pk=self.instance.module_id)

        # En modification, garantir que le module existant reste selectionnable.
        if self.instance and self.instance.pk and self.instance.module_id:
            self.fields['module'].queryset = Module.objects.filter(
                Q(pk__in=self.fields['module'].queryset.values_list('pk', flat=True))
                | Q(pk=self.instance.module_id)
            ).distinct().order_by('nom')

        if self.instance and self.instance.pk and self.instance.module_id and filiere_id:
            current_programme = (
                self.instance.module.programmes_principaux.filter(filiere_id=filiere_id)
                .order_by('nom')
                .first()
            )
            if current_programme:
                self.fields['programme'].queryset = Programme.objects.filter(
                    Q(pk__in=self.fields['programme'].queryset.values_list('pk', flat=True))
                    | Q(pk=current_programme.pk)
                ).distinct().order_by('nom')
                if not self.is_bound:
                    self.fields['programme'].initial = current_programme.pk

        module_id = (
            self.data.get('module')
            or self.initial.get('module')
            or getattr(self.instance, 'module_id', None)
        )
        if module_id:
            module = Module.objects.filter(pk=module_id).first()
            if module:
                self.fields['nombre_heures'].initial = module.nombre_heures

        if not self.is_bound and self.instance and self.instance.pk:
            if self.instance.date_debut:
                self.fields['date_debut'].initial = self.instance.date_debut.strftime('%Y-%m-%d')
            if self.instance.date_fin:
                self.fields['date_fin'].initial = self.instance.date_fin.strftime('%Y-%m-%d')

    def clean(self):
        cleaned_data = super().clean()
        professeur = cleaned_data.get('professeur')
        etablissement = cleaned_data.get('etablissement')
        filiere = cleaned_data.get('filiere')
        programme = cleaned_data.get('programme')
        module = cleaned_data.get('module')
        date_debut = cleaned_data.get('date_debut')
        date_fin = cleaned_data.get('date_fin')
        heures_affectees = cleaned_data.get('heures_affectees')

        cleaned_data['nombre_heures'] = module.nombre_heures if module else 0
        if not heures_affectees and module:
            heures_affectees = module.nombre_heures
            cleaned_data['heures_affectees'] = heures_affectees

        if professeur and heures_affectees is not None:
            affectations_prof = professeur.affectations.filter(actif=True)
            if self.instance and self.instance.pk:
                affectations_prof = affectations_prof.exclude(pk=self.instance.pk)

            if date_debut:
                conflits_planning = affectations_prof
                if date_fin:
                    conflits_planning = conflits_planning.filter(
                        date_debut__lte=date_fin
                    ).filter(
                        Q(date_fin__isnull=True) | Q(date_fin__gte=date_debut)
                    )
                else:
                    conflits_planning = conflits_planning.filter(
                        Q(date_fin__isnull=True) | Q(date_fin__gte=date_debut)
                    )
                if conflits_planning.exists():
                    conflit = conflits_planning.order_by('date_debut').first()
                    periode_fin = conflit.date_fin.strftime('%d/%m/%Y') if conflit.date_fin else 'en cours'
                    self.add_error(
                        'date_debut',
                        f"Ce professeur est déjà occupé du {conflit.date_debut.strftime('%d/%m/%Y')} au {periode_fin}."
                    )

            heures_prof_deja_affectees = sum(a.heures_affectees for a in affectations_prof)
            heures_restantes_prof = max((professeur.quota_heures or 0) - heures_prof_deja_affectees, 0)

            if heures_affectees > heures_restantes_prof:
                self.add_error(
                    'heures_affectees',
                    f"Le professeur sélectionné ne dispose plus que de {heures_restantes_prof}h restantes."
                )

        if programme and filiere and programme.filiere_id != filiere.id:
            self.add_error('programme', "Le programme sélectionné n'appartient pas à la filière choisie.")

        if module and programme:
            if not programme.module_formation.filter(pk=module.pk).exists():
                self.add_error('module', "Le module sélectionné n'appartient pas au programme choisi.")

        if module and heures_affectees is not None:
            affectations_module = module.affectations.filter(actif=True)
            if etablissement:
                affectations_module = affectations_module.filter(etablissement=etablissement)
            if filiere:
                affectations_module = affectations_module.filter(filiere=filiere)
            if self.instance and self.instance.pk:
                affectations_module = affectations_module.exclude(pk=self.instance.pk)

            heures_module_deja_couvertes = sum(a.heures_affectees for a in affectations_module)
            heures_restantes_module = max((module.nombre_heures or 0) - heures_module_deja_couvertes, 0)

            if heures_affectees > heures_restantes_module:
                self.add_error(
                    'heures_affectees',
                    f"Ce besoin ne peut plus recevoir que {heures_restantes_module}h sur cette filière."
                )
        return cleaned_data

    class Meta:
        model = Affectation
        fields = ['professeur', 'etablissement', 'filiere', 'programme', 'module', 'nombre_heures', 'heures_affectees', 'priorite', 'date_debut', 'date_fin', 'observations', 'actif']
        widgets = {
            'professeur': forms.Select(attrs={'class': 'form-control'}),
            'etablissement': forms.Select(attrs={'class': 'form-control'}),
            'filiere': forms.Select(attrs={'class': 'form-control'}),
            'programme': forms.Select(attrs={'class': 'form-control'}),
            'module': forms.Select(attrs={'class': 'form-control'}),
            'heures_affectees': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Heures affectées'}),
            'priorite': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(format='%Y-%m-%d', attrs={'class': 'form-control', 'type': 'date'}),
            'observations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observations'}),
            'actif': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
