from django.contrib.auth.models import AbstractUser
from django.db import models
from apps.organigramme.models import Structure

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
        ("admin_ministere", "Admin Ministère"),
        ("chef_direction", "Chef de Direction"),
        ("chef_service", "Chef de Service"),
        ("agent", "Agent"),
        ("rh", "RH"),
    ]

    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default="agent")

    def __str__(self):
        return f"{self.username} ({self.role})"