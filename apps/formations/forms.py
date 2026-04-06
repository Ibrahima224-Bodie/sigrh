from django import forms
from .models import Formation, Certificat
from apps.agents.models import Agent

class FormationForm(forms.ModelForm):
    class Meta:
        model = Formation
        fields = '__all__'
        labels = {
            'titre': 'Titre',
            'description': 'Description',
            'organisme': 'Organisme',
            'date_debut': 'Date de Début',
            'date_fin': 'Date de Fin',
            'lieu': 'Lieu',
            'participants': 'Participants',
        }
        widgets = {
            'titre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Titre'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Description'}),
            'organisme': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Organisme'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'lieu': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Lieu'}),
            'participants': forms.CheckboxSelectMultiple(attrs={'class': 'form-check'}),
        }

class CertificatForm(forms.ModelForm):
    formation = forms.ModelChoiceField(
        queryset=Formation.objects.order_by('titre'),
        label='Formation',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    agent = forms.ModelChoiceField(
        queryset=Agent.objects.order_by('nom', 'prenom'),
        label='Agent',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Certificat
        fields = ['formation', 'agent', 'date_obtention', 'fichier']
        labels = {
            'date_obtention': 'Date d\'Obtention',
            'fichier': 'Fichier',
        }
        widgets = {
            'date_obtention': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
        }
