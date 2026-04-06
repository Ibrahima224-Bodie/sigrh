from django import forms
from .models import Agent
from apps.organigramme.models import Structure

class AgentForm(forms.ModelForm):
    service = forms.ModelChoiceField(
        queryset=Structure.objects.order_by('nom'),
        required=False,
        empty_label='Sélectionner un service',
        label='Service',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Agent
        fields = ['matricule', 'nom', 'prenom', 'telephone', 'email', 'fonction', 'service', 'date_recrutement', 'photo']
        labels = {
            'matricule': 'Matricule',
            'nom': 'Nom',
            'prenom': 'Prénom',
            'telephone': 'Téléphone',
            'email': 'Email',
            'fonction': 'Fonction',
            'date_recrutement': 'Date de Recrutement',
            'photo': 'Photo',
        }
        widgets = {
            'matricule': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Matricule'}),
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'prenom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'fonction': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Fonction'}),
            'date_recrutement': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'photo': forms.FileInput(attrs={'class': 'form-control'}),
        }

