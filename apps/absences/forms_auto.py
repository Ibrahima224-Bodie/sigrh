from django import forms
from .models import Conge
from apps.agents.models import Agent
from apps.enseignants.models import Professeur


class CongeAutoForm(forms.ModelForm):
    """
    Formulaire simplifié pour que les agents et professeurs demandent un congé pour eux-mêmes.
    Les champs agent/professeur et établissement sont pré-remplis automatiquement.
    """

    def __init__(self, *args, **kwargs):
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)

    def _resolve_agent_for_user(self, user):
        if not user:
            return None

        email = (user.email or '').strip()
        username = (user.username or '').strip()
        first_name = (user.first_name or '').strip()
        last_name = (user.last_name or '').strip()

        if email:
            agent = Agent.objects.filter(email__iexact=email).first()
            if agent:
                return agent

        if username and '@' in username:
            agent = Agent.objects.filter(email__iexact=username).first()
            if agent:
                return agent

        if username:
            agent = Agent.objects.filter(matricule__iexact=username).first()
            if agent:
                return agent

        if first_name and last_name:
            agent = Agent.objects.filter(nom__iexact=last_name, prenom__iexact=first_name).first()
            if agent:
                return agent
            agent = Agent.objects.filter(nom__iexact=first_name, prenom__iexact=last_name).first()
            if agent:
                return agent

        return None

    def _resolve_professeur_for_user(self, user):
        if not user:
            return None

        email = (user.email or '').strip()
        username = (user.username or '').strip()
        first_name = (user.first_name or '').strip()
        last_name = (user.last_name or '').strip()

        if email:
            professeur = Professeur.objects.filter(email__iexact=email).first()
            if professeur:
                return professeur

        if username and '@' in username:
            professeur = Professeur.objects.filter(email__iexact=username).first()
            if professeur:
                return professeur

        if username:
            professeur = Professeur.objects.filter(matricule__iexact=username).first()
            if professeur:
                return professeur

        if first_name and last_name:
            professeur = Professeur.objects.filter(nom__iexact=last_name, prenom__iexact=first_name).first()
            if professeur:
                return professeur
            professeur = Professeur.objects.filter(nom__iexact=first_name, prenom__iexact=last_name).first()
            if professeur:
                return professeur

        return None

    def clean(self):
        cleaned_data = super().clean()

        user = self.current_user
        if not user:
            return cleaned_data

        agent = self._resolve_agent_for_user(user)
        professeur = self._resolve_professeur_for_user(user)
        preferred_role = getattr(user, 'role', None)

        if preferred_role == 'agent' and agent:
            self.instance.agent = agent
            self.instance.professeur = None
            self.instance.etablissement = None
        elif preferred_role == 'professeur' and professeur:
            self.instance.professeur = professeur
            self.instance.agent = None
            self.instance.etablissement = professeur.etablissement
        elif agent and not professeur:
            self.instance.agent = agent
            self.instance.professeur = None
            self.instance.etablissement = None
        elif professeur and not agent:
            self.instance.professeur = professeur
            self.instance.agent = None
            self.instance.etablissement = professeur.etablissement
        elif agent and professeur:
            raise forms.ValidationError(
                "Ce compte correspond à plusieurs profils. Contactez l'administrateur pour préciser le profil autorisé."
            )
        else:
            raise forms.ValidationError(
                "Aucun profil agent ou professeur n'est lié à ce compte utilisateur."
            )

        return cleaned_data
    
    class Meta:
        model = Conge
        fields = ['type_conge', 'date_debut', 'date_fin', 'motif']
        labels = {
            'type_conge': 'Type de Congé',
            'date_debut': 'Date de Début',
            'date_fin': 'Date de Fin',
            'motif': 'Motif',
        }
        widgets = {
            'type_conge': forms.Select(attrs={'class': 'form-control'}),
            'date_debut': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'date_fin': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'motif': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Décrivez le motif de votre demande de congé'}),
        }
