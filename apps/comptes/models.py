from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.organigramme.models import Structure
from .role_groups import sync_user_role_group

class User(AbstractUser):
    # Lier un utilisateur à une structure
    structure = models.ForeignKey(
        Structure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="utilisateurs"
    )

    # Définir un rôle
    ROLE_CHOICES = [
        ("administrateur", "Administrateur"),
        ("directeur_ecole", "Directeur d'ecole"),
        ("chef_service_drh", "Chef service DRH"),
        ("secretaire_general", "Secretaire general"),
        ("chef_cabinet", "Chef de cabinet"),
        ("ministre", "Ministre"),
        ("technicien_drh", "Technicien DRH"),
        ("agent", "Agent"),
        ("professeur", "Professeur"),
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="professeur")
    photo = models.ImageField(upload_to="users/photos/", blank=True, null=True)

    class Meta(AbstractUser.Meta):
        permissions = [
            ('toggle_user_activation', "Peut activer ou désactiver un utilisateur"),
            ('manage_role_permissions', "Peut gérer les permissions des rôles"),
        ]

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        sync_user_role_group(self)
        if not getattr(self, '_photo_syncing', False):
            update_fields = kwargs.get('update_fields')
            if update_fields is None or 'photo' in update_fields:
                self._sync_photo_to_profile()

    def _sync_photo_to_profile(self):
        from django.apps import apps
        new_name = self.photo.name if self.photo else ''
        role = getattr(self, 'role', '')
        if role == 'professeur':
            try:
                Professeur = apps.get_model('enseignants', 'Professeur')
            except LookupError:
                return
            prof = None
            if self.email:
                prof = Professeur.objects.filter(email__iexact=self.email).first()
            if prof is None:
                prof = Professeur.objects.filter(matricule__iexact=self.username).first()
            if prof:
                old_name = prof.photo.name if prof.photo else ''
                if old_name != new_name:
                    prof._photo_syncing = True
                    prof.photo = self.photo
                    prof.save(update_fields=['photo'])
        elif role == 'agent':
            try:
                Agent = apps.get_model('agents', 'Agent')
            except LookupError:
                return
            agent = None
            if self.email:
                agent = Agent.objects.filter(email__iexact=self.email).first()
            if agent is None:
                agent = Agent.objects.filter(matricule__iexact=self.username).first()
            if agent:
                old_name = agent.photo.name if agent.photo else ''
                if old_name != new_name:
                    agent._photo_syncing = True
                    agent.photo = self.photo
                    agent.save(update_fields=['photo'])

    def __str__(self):
        return f"{self.username} ({self.role})"