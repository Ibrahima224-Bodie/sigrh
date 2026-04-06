from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.agents.models import Agent
from apps.enseignants.models import Professeur

User = get_user_model()

class Conge(models.Model):

    TYPE_CONGE = [
        ("annuel", "Congé Annuel"),
        ("maladie", "Congé Maladie"),
        ("maternite", "Congé Maternité"),
        ("permission", "Permission"),
        ("formation", "Congé pour Formation"),
    ]

    STATUT_CHOICES = [
        ("demande", "Demande en cours"),
        ("approuve_directeur", "Approuvé par directeur"),
        ("approuve_drh", "Approuvé par DRH"),
        ("refuse", "Refusé"),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, null=True, blank=True, related_name='conges')
    professeur = models.ForeignKey(Professeur, on_delete=models.CASCADE, null=True, blank=True, related_name='conges')
    user_demandeur = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conges_demandes', null=True, blank=True)
    etablissement = models.ForeignKey('enseignants.Etablissement', on_delete=models.SET_NULL, null=True, blank=True, related_name='conges')

    type_conge = models.CharField(max_length=50, choices=TYPE_CONGE)

    date_debut = models.DateField()
    date_fin = models.DateField()

    motif = models.TextField()

    statut = models.CharField(
        max_length=30,
        choices=STATUT_CHOICES,
        default="demande"
    )

    # Approbations
    approuve_directeur_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_approuves_directeur'
    )
    date_approbation_directeur = models.DateTimeField(null=True, blank=True)

    approuve_drh_par = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name='conges_approuves_drh'
    )
    date_approbation_drh = models.DateTimeField(null=True, blank=True)

    date_creation = models.DateTimeField(default=timezone.now, null=True, blank=True)
    date_modification = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ("demander_conge", "Peut demander un congé"),
            ("commenter_conge", "Peut commenter une demande de congé"),
            ("approuver_conge_directeur", "Peut approuver un congé au niveau directeur"),
            ("valider_conge_drh", "Peut valider un congé au niveau DRH"),
        ]

    def get_overlapping_conges_queryset(self):
        queryset = Conge.objects.exclude(pk=self.pk).exclude(statut='refuse')

        if self.agent_id:
            queryset = queryset.filter(agent_id=self.agent_id)
        elif self.professeur_id:
            queryset = queryset.filter(professeur_id=self.professeur_id)
        else:
            return Conge.objects.none()

        if self.date_debut and self.date_fin:
            queryset = queryset.filter(
                date_debut__lte=self.date_fin,
                date_fin__gte=self.date_debut,
            )

        return queryset

    def clean(self):
        super().clean()
        if bool(self.agent) == bool(self.professeur):
            raise ValidationError("Un congé doit être rattaché soit à un agent, soit à un professeur.")
        if self.date_debut and self.date_fin and self.date_fin < self.date_debut:
            raise ValidationError("La date de fin doit être supérieure ou égale à la date de début.")
        if self.date_debut and self.date_fin and self.get_overlapping_conges_queryset().exists():
            raise ValidationError(
                "Cette personne possède déjà une demande de congé sur un intervalle de dates qui se chevauche."
            )

    @property
    def beneficiaire(self):
        return self.agent or self.professeur

    @property
    def beneficiaire_nom(self):
        beneficiaire = self.beneficiaire
        if not beneficiaire:
            return ""
        return f"{beneficiaire.nom} {beneficiaire.prenom}".strip()

    @property
    def beneficiaire_type(self):
        if self.professeur_id:
            return "Professeur"
        if self.agent_id:
            return "Agent"
        return ""

    @property
    def beneficiaire_poste(self):
        if self.professeur_id:
            return self.professeur.specialite
        if self.agent_id:
            return self.agent.fonction
        return ""

    @property
    def beneficiaire_email(self):
        beneficiaire = self.beneficiaire
        return getattr(beneficiaire, 'email', '') if beneficiaire else ''

    def __str__(self):
        return f"{self.beneficiaire_nom} - {self.get_type_conge_display()}"


class CommentaireConge(models.Model):
    """Annotations et commentaires sur une demande de congé"""
    conge = models.ForeignKey(Conge, on_delete=models.CASCADE, related_name='commentaires')
    auteur = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='commentaires_conge')
    texte = models.TextField()
    date_creation = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-date_creation']

    def __str__(self):
        return f"Commentaire de {self.auteur.username} - {self.date_creation}"