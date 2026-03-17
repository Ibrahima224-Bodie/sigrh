from django.db import models
from apps.agents.models import Agent

class Carriere(models.Model):

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)

    grade = models.CharField(max_length=100)
    poste = models.CharField(max_length=150)

    date_debut = models.DateField()
    date_fin = models.DateField(null=True, blank=True)

    decision = models.FileField(upload_to="carrieres/decisions/", blank=True)

    def __str__(self):
        return f"{self.agent} - {self.grade}"