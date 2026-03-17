from django.db import models
from apps.organigramme.models import Structure


class Agent(models.Model):

    matricule = models.CharField(max_length=50, unique=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    telephone = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    fonction = models.CharField(max_length=150, blank=True)
    service = models.ForeignKey(Structure, on_delete=models.SET_NULL, null=True, blank=True)
    date_recrutement = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to='agents/photos/', blank=True, null=True)

    def __str__(self):
        return f"{self.nom} {self.prenom}"
    