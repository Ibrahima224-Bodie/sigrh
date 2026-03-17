from django import forms
from .models import Conge
from apps.agents.models import Agent

class CongeForm(forms.ModelForm):
    agent_text = forms.CharField(
        required=True,
        label='Agent',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tapez ou sélectionnez un agent',
            'list': 'agent-list'
        })
    )
    
    class Meta:
        model = Conge
        fields = ['date_debut', 'date_fin', 'type_conge', 'motif', 'statut']
        labels = {
            'date_debut': 'Date de Début',
            'date_fin': 'Date de Fin',
            'type_conge': 'Type de Congé',
            'motif': 'Motif',
            'statut': 'Statut',
        }
        widgets = {
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'type_conge': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tapez ou sélectionnez un type', 'list': 'type-conge-list'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Motif'}),
            'statut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tapez ou sélectionnez un statut', 'list': 'statut-list'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.agent:
            self.fields['agent_text'].initial = f"{self.instance.agent.nom} {self.instance.agent.prenom}"

    def save(self, commit=True):
        instance = super().save(commit=False)
        agent_text = self.cleaned_data.get('agent_text')
        if agent_text:
            # Essayer de trouver l'agent par nom complet
            try:
                nom, prenom = agent_text.split(' ', 1)
                agent = Agent.objects.get(nom=nom, prenom=prenom)
                instance.agent = agent
            except (ValueError, Agent.DoesNotExist):
                # Si pas trouvé, créer un nouvel agent ou gérer l'erreur
                pass
        if commit:
            instance.save()
        return instance
