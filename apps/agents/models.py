from django.db import models

from apps.organigramme.models import Structure


class Agent(models.Model):
    matricule = models.CharField(
        max_length=50,
        unique=True,
        error_messages={
            'unique': 'Ce matricule est deja utilise.',
        },
    )
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(
        max_length=20,
        unique=True,
        error_messages={
            'unique': 'Ce numero de telephone est deja utilise.',
        },
    )
    email = models.EmailField(
        max_length=50,
        unique=True,
        error_messages={
            'unique': 'Ce mail est deja utilise.',
        },
    )
    fonction = models.CharField(max_length=150, blank=True)
    service = models.ForeignKey(
        Structure,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agents',
    )
    date_recrutement = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='agents/photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not getattr(self, '_photo_syncing', False):
            update_fields = kwargs.get('update_fields')
            if update_fields is None or 'photo' in update_fields:
                self._sync_photo_to_user()

    def _sync_photo_to_user(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = None
        if self.email:
            user = User.objects.filter(email__iexact=self.email).first()
        if user is None and self.matricule:
            user = User.objects.filter(username__iexact=self.matricule).first()
        if user is None:
            return
        old_name = user.photo.name if user.photo else ''
        new_name = self.photo.name if self.photo else ''
        if old_name == new_name:
            return
        user._photo_syncing = True
        user.photo = self.photo
        user.save(update_fields=['photo'])
