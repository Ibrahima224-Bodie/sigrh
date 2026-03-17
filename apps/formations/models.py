from django.db import models
from apps.agents.models import Agent

class Formation(models.Model):
    titre = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    organisme = models.CharField(max_length=150)
    date_debut = models.DateField()
    date_fin = models.DateField()
    lieu = models.CharField(max_length=150)

    participants = models.ManyToManyField(
        Agent,
        related_name="formations",
        blank=True
    )

    def __str__(self):
        return self.titre

class Certificat(models.Model):
    formation = models.ForeignKey(Formation, on_delete=models.CASCADE, related_name="certificats")
    agent = models.ForeignKey(Agent, on_delete=models.CASCADE, related_name="certificats")
    date_obtention = models.DateField()
    fichier = models.FileField(upload_to="formations/certificats/", blank=True)

    def __str__(self):
        return f"{self.agent} - {self.formation.titre}"