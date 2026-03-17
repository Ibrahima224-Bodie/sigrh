from django.db import models
from apps.agents.models import Agent

class Conge(models.Model):

    TYPE_CONGE = [
        ("annuel", "Congé Annuel"),
        ("maladie", "Congé Maladie"),
        ("maternite", "Congé Maternité"),
        ("permission", "Permission"),
        ("formation", "Congé pour Formation"),
    ]

    agent = models.ForeignKey(Agent, on_delete=models.CASCADE)

    type_conge = models.CharField(max_length=50, choices=TYPE_CONGE)

    date_debut = models.DateField()
    date_fin = models.DateField()

    motif = models.TextField()

    statut = models.CharField(
        max_length=20,
        choices=[
            ("en_attente", "En attente"),
            ("approuve", "Approuvé"),
            ("refuse", "Refusé"),
        ],
        default="en_attente"
    )