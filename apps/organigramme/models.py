from django.db import models

class Structure(models.Model):

    TYPE_STRUCTURE = [
        ("direction", "Direction"),
        ("service", "Service"),
        ("division", "Division"),
        ("section", "Section"),
    ]

    nom = models.CharField(max_length=200)
    sigle = models.CharField(max_length=50, blank=True)

    type_structure = models.CharField(
        max_length=50,
        choices=TYPE_STRUCTURE
    )

    structure_parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sous_structures"
    )

    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nom} ({self.type_structure})"