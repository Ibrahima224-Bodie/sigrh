from django import forms
from .models import Carriere
from apps.agents.models import Agent

class CarriereForm(forms.ModelForm):
    agent = forms.ModelChoiceField(
        queryset=Agent.objects.order_by('nom', 'prenom'),
        label='Agent',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Carriere
        fields = ['agent', 'grade', 'poste', 'date_debut', 'date_fin', 'decision']
        labels = {
            'grade': 'Grade',
            'poste': 'Poste',
            'date_debut': 'Date de Début',
            'date_fin': 'Date de Fin',
            'decision': 'Décision',
        }
        widgets = {
            'grade': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Grade'}),
            'poste': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Poste'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'decision': forms.FileInput(attrs={'class': 'form-control'}),
        }

