from django import forms
from .models import Carriere
from apps.agents.models import Agent

class CarriereForm(forms.ModelForm):
    agent_text = forms.CharField(
        required=True,
        label='Agent',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tapez ou sélectionnez un agent',
            'list': 'agent-carriere-list'
        })
    )
    
    class Meta:
        model = Carriere
        fields = ['grade', 'poste', 'date_debut', 'date_fin', 'decision']
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.agent:
            self.fields['agent_text'].initial = f"{self.instance.agent.nom} {self.instance.agent.prenom}"

    def save(self, commit=True):
        instance = super().save(commit=False)
        agent_text = self.cleaned_data.get('agent_text')
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
