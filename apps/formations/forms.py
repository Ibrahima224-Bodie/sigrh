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
    formation_text = forms.CharField(
        required=True,
        label='Formation',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tapez ou sélectionnez une formation',
            'list': 'formation-list'
        })
    )
    agent_text = forms.CharField(
        required=True,
        label='Agent',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tapez ou sélectionnez un agent',
            'list': 'agent-certificat-list'
        })
    )
    
    class Meta:
        model = Certificat
        fields = ['date_obtention', 'fichier']
        labels = {
            'date_obtention': 'Date d\'Obtention',
            'fichier': 'Fichier',
        }
        widgets = {
            'date_obtention': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'fichier': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            if self.instance.formation:
                self.fields['formation_text'].initial = self.instance.formation.titre
            if self.instance.agent:
                self.fields['agent_text'].initial = f"{self.instance.agent.nom} {self.instance.agent.prenom}"

    def save(self, commit=True):
        instance = super().save(commit=False)
        formation_text = self.cleaned_data.get('formation_text')
        agent_text = self.cleaned_data.get('agent_text')
        
        if formation_text:
            try:
                formation = Formation.objects.get(titre=formation_text)
                instance.formation = formation
            except Formation.DoesNotExist:
                pass
        
        if agent_text:
            try:
                nom, prenom = agent_text.split(' ', 1)
                agent = Agent.objects.get(nom=nom, prenom=prenom)
                instance.agent = agent
            except (ValueError, Agent.DoesNotExist):
                pass
        
        if commit:
            instance.save()
        return instance
