from django import forms
from .models import Agent
from apps.organigramme.models import Structure

class AgentForm(forms.ModelForm):
    service_text = forms.CharField(
        required=False,
        label='Service',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tapez ou sélectionnez un service',
            'list': 'service-list'
        })
    )
    
    class Meta:
        model = Agent
        fields = ['matricule', 'nom', 'prenom', 'telephone', 'email', 'fonction', 'date_recrutement', 'photo']
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.service:
            self.fields['service_text'].initial = self.instance.service.nom

    def save(self, commit=True):
        instance = super().save(commit=False)
        service_text = self.cleaned_data.get('service_text')
        if service_text:
            structure, created = Structure.objects.get_or_create(nom=service_text)
            instance.service = structure
        else:
            instance.service = None
        if commit:
            instance.save()
        return instance
