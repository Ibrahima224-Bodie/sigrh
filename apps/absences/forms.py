from django import forms
from .models import Conge, CommentaireConge
from apps.agents.models import Agent
from apps.enseignants.models import Professeur

class CongeForm(forms.ModelForm):
    agent = forms.ChoiceField(
        label='Agent / Professeur',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Conge
        fields = ['date_debut', 'date_fin', 'type_conge', 'motif']
        labels = {
            'date_debut': 'Date de Début',
            'date_fin': 'Date de Fin',
            'type_conge': 'Type de Congé',
            'motif': 'Motif',
        }
        widgets = {
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'type_conge': forms.Select(attrs={'class': 'form-control'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Motif'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        agent_choices = [
            (f'agent:{agent.pk}', f"Agent - {agent.nom} {agent.prenom}")
            for agent in Agent.objects.order_by('nom', 'prenom')
        ]
        professeur_choices = [
            (f'professeur:{professeur.pk}', f"Professeur - {professeur.nom} {professeur.prenom}")
            for professeur in Professeur.objects.order_by('nom', 'prenom')
        ]
        self.fields['agent'].choices = [
            ('', 'Sélectionner un agent ou un professeur'),
            ('Agents', agent_choices),
            ('Professeurs', professeur_choices),
        ]

        self._selected_kind = None
        self._selected_beneficiaire = None
        if self.instance.pk:
            if self.instance.agent_id:
                self.initial['agent'] = f'agent:{self.instance.agent_id}'
            elif self.instance.professeur_id:
                self.initial['agent'] = f'professeur:{self.instance.professeur_id}'

    def clean_agent(self):
        value = self.cleaned_data['agent']
        kind, _, identifier = value.partition(':')
        if kind not in {'agent', 'professeur'} or not identifier.isdigit():
            raise forms.ValidationError("Sélection invalide.")

        object_id = int(identifier)
        if kind == 'agent':
            beneficiaire = Agent.objects.filter(pk=object_id).first()
        else:
            beneficiaire = Professeur.objects.filter(pk=object_id).first()

        if beneficiaire is None:
            raise forms.ValidationError("La personne sélectionnée est introuvable.")

        self._selected_kind = kind
        self._selected_beneficiaire = beneficiaire
        return value

    def clean(self):
        cleaned_data = super().clean()
        if self._selected_kind == 'agent':
            self.instance.agent = self._selected_beneficiaire
            self.instance.professeur = None
        elif self._selected_kind == 'professeur':
            self.instance.professeur = self._selected_beneficiaire
            self.instance.agent = None
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.agent = self._selected_beneficiaire if self._selected_kind == 'agent' else None
        instance.professeur = self._selected_beneficiaire if self._selected_kind == 'professeur' else None
        if commit:
            instance.save()
            self.save_m2m()
        return instance


class CommentaireCongeForm(forms.ModelForm):
    class Meta:
        model = CommentaireConge
        fields = ['texte']
        labels = {'texte': 'Commentaire / Annotation'}
        widgets = {'texte': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Écrivez votre annotation...'})}


class ApprobationDirecteurForm(forms.Form):
    """Formulaire pour l'approbation du directeur"""
    ACTION_CHOICES = [('approuver', 'Approuver'), ('refuser', 'Refuser')]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect)
    commentaire = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Commentaire (optionnel)'}),
        label='Annotation'
    )


class ApprobationDRHForm(forms.Form):
    """Formulaire pour la validation de la DRH"""
    ACTION_CHOICES = [('approuver', 'Approuver'), ('refuser', 'Refuser')]
    action = forms.ChoiceField(choices=ACTION_CHOICES, widget=forms.RadioSelect)
    commentaire = forms.CharField(
        required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Commentaire (optionnel)'}),
        label='Annotation'
    )
