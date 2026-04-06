from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
import unicodedata


class Region(models.Model):
    nom = models.CharField(max_length=150, unique=True)

    class Meta:
        db_table = 'region'
        ordering = ['nom']
        verbose_name = "Région"
        verbose_name_plural = "Régions"
        permissions = [
            ('csv_regions', "Peut importer/exporter des données CSV Régions"),
        ]

    def __str__(self):
        return self.nom


class Prefecture(models.Model):
    region = models.ForeignKey(Region, on_delete=models.CASCADE, related_name='prefectures')
    nom = models.CharField(max_length=150)

    class Meta:
        db_table = 'prefecture'
        ordering = ['region', 'nom']
        unique_together = ['region', 'nom']
        verbose_name = "Préfecture"
        verbose_name_plural = "Préfectures"
        permissions = [
            ('csv_prefectures', "Peut importer/exporter des données CSV Préfectures"),
        ]

    def __str__(self):
        return f"{self.nom} ({self.region.nom})"


class Commune(models.Model):
    prefecture = models.ForeignKey(Prefecture, on_delete=models.CASCADE, related_name='communes')
    nom = models.CharField(max_length=150)

    class Meta:
        db_table = 'commune'
        ordering = ['prefecture', 'nom']
        unique_together = ['prefecture', 'nom']
        verbose_name = "Commune"
        verbose_name_plural = "Communes"
        permissions = [
            ('csv_communes', "Peut importer/exporter des données CSV Communes"),
        ]

    def __str__(self):
        return f"{self.nom} ({self.prefecture.nom})"


class Quartier(models.Model):
    commune = models.ForeignKey(Commune, on_delete=models.CASCADE, related_name='quartiers')
    nom = models.CharField(max_length=150)

    class Meta:
        db_table = 'quartier'
        ordering = ['commune', 'nom']
        unique_together = ['commune', 'nom']
        verbose_name = "Quartier / District"
        verbose_name_plural = "Quartiers / Districts"
        permissions = [
            ('csv_quartiers', "Peut importer/exporter des données CSV Quartiers"),
        ]

    def __str__(self):
        return f"{self.nom} ({self.commune.nom})"


class Secteur(models.Model):
    quartier = models.ForeignKey(
        Quartier,
        on_delete=models.CASCADE,
        related_name='secteurs'
    )
    nom = models.CharField(max_length=150)

    class Meta:
        db_table = 'secteur'
        ordering = ['quartier', 'nom']
        verbose_name = "Secteur"
        verbose_name_plural = "Secteurs"
        permissions = [
            ('csv_secteurs', "Peut importer/exporter des données CSV Secteurs"),
        ]

    def __str__(self):
        return f"{self.nom} ({self.quartier.nom})"


def _letters_upper(value):
    if not value:
        return ""
    normalized = unicodedata.normalize('NFKD', value)
    return ''.join(ch for ch in normalized if ch.isalpha()).upper()

class Etablissement(models.Model):
    """Représente un établissement d'enseignement"""
    nom = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50, unique=True, blank=True, null=True)
    localisation = models.CharField(max_length=200, blank=True, null=True)
    contact = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    directeur = models.CharField(max_length=100, blank=True, null=True)
    date_creation = models.DateField(blank=True, null=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True, related_name='etablissements')
    prefecture = models.ForeignKey(Prefecture, on_delete=models.SET_NULL, null=True, blank=True, related_name='etablissements')
    commune = models.ForeignKey(Commune, on_delete=models.SET_NULL, null=True, blank=True, related_name='etablissements')
    quartier = models.ForeignKey(Quartier, on_delete=models.SET_NULL, null=True, blank=True, related_name='etablissements')
    secteur = models.ForeignKey(Secteur, on_delete=models.SET_NULL, null=True, blank=True, related_name='etablissements')
    
    class Meta:
        db_table = 'etablissement'
        verbose_name = "Établissement"
        verbose_name_plural = "Établissements"
        ordering = ['nom']
        permissions = [
            ('access_geo_filters', "Peut utiliser les filtres géographiques"),
        ]

    def save(self, *args, **kwargs):
        if self.region_id and self.nom:
            region_nom = self.region.nom if getattr(self, 'region', None) else Region.objects.filter(pk=self.region_id).values_list('nom', flat=True).first()
            region_part = _letters_upper(region_nom)[:3].ljust(3, 'X')
            etab_part = _letters_upper(self.nom)[:3].ljust(3, 'X')
            base_code = f"{region_part}{etab_part}"
            generated_code = base_code
            suffix = 1
            while Etablissement.objects.exclude(pk=self.pk).filter(code=generated_code).exists():
                suffix += 1
                generated_code = f"{base_code}{suffix}"
            self.code = generated_code
        elif self.code == '':
            self.code = None
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.nom} ({self.code})"


class Filiere(models.Model):
    """Représente une filière d'études"""
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name="filieres", null=True, blank=True)
    etablissements = models.ManyToManyField(Etablissement, related_name='filieres_partagees', blank=True)
    duree_mois = models.IntegerField(default=12, help_text="Durée en mois")
    nombre_heures_total = models.IntegerField(default=500, help_text="Total d'heures requises")
    date_creation = models.DateField(auto_now_add=True)
    programme = models.ForeignKey('Programme', on_delete=models.SET_NULL, null=True, blank=True, related_name='filieres_associees')
    
    class Meta:
        db_table = 'filiere'
        verbose_name = "Filière"
        verbose_name_plural = "Filières"
        ordering = ['nom']
        permissions = [
            ('filter_filieres_by_etablissement', "Peut filtrer les filières par établissement"),
        ]

    def get_primary_etablissement(self):
        principal = self.etablissements.order_by('nom').first()
        if principal:
            return principal
        return self.etablissement

    def has_etablissement(self, etablissement_id):
        if not etablissement_id:
            return False
        return self.etablissements.filter(pk=etablissement_id).exists() or self.etablissement_id == etablissement_id
    
    def __str__(self):
        etablissement = self.get_primary_etablissement()
        code = etablissement.code if etablissement else '-'
        return f"{self.nom} - {code}"


class Programme(models.Model):
    """Représente un programme au sein d'une filière"""
    nom = models.CharField(max_length=200)
    code = models.CharField(max_length=50)
    filiere = models.ForeignKey(Filiere, on_delete=models.SET_NULL, null=True, blank=True, related_name="programmes")
    description = models.TextField(blank=True)
    semestre = models.IntegerField(help_text="Numéro du semestre")
    nombre_heures = models.IntegerField(default=100, help_text="Nombre d'heures total du programme")
    ordre = models.IntegerField(default=1, help_text="Ordre d'apparition")
    module_formation = models.ManyToManyField('Module', blank=True, related_name='programmes_principaux')
    
    class Meta:
        db_table = 'programme'
        verbose_name = "Programme"
        verbose_name_plural = "Programmes"
        ordering = ['filiere', 'semestre', 'ordre']
        unique_together = ['filiere', 'code']
        permissions = [
            ('csv_programmes', "Peut importer/exporter des données CSV Programmes"),
        ]
    
    def __str__(self):
        if self.filiere_id:
            return f"{self.filiere.nom} - {self.nom} (Sem {self.semestre})"
        return f"{self.nom} (Sem {self.semestre})"


class Module(models.Model):
    """Représente un module au sein d'un programme"""
    nom = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    nombre_heures = models.IntegerField(default=20, help_text="Nombre d'heures du module")
    ordre = models.IntegerField(default=1, help_text="Ordre d'apparition")
    
    class Meta:
        db_table = 'module'
        verbose_name = "Module"
        verbose_name_plural = "Modules"
        ordering = ['nom', 'ordre']
        permissions = [
            ('view_besoin', "Peut consulter les besoins d'enseignement"),
            ('view_besoin_suggestions', "Peut consulter les suggestions de professeurs pour les besoins"),
            ('csv_modules', "Peut importer/exporter des données CSV Modules"),
            ('filter_modules_by_filiere', "Peut filtrer les modules par filière"),
        ]
    
    def __str__(self):
        return self.nom


class Professeur(models.Model):
    """Représente un professeur/formateur"""
    STATUT_CHOICES = [
        ('permanent', 'Fonctionnaire'),
        ('contractuel', 'Contractuel'),
        ('vacataire', 'Vacataire'),
        ('autre', 'Autre'),
    ]

    SEXE_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
    ]
    
    matricule = models.CharField(max_length=50, unique=True, blank=True, null=True)
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    sexe = models.CharField(max_length=1, choices=SEXE_CHOICES, blank=True)
    hierarchie = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    telephone = models.CharField(max_length=20, blank=True)
    photo = models.ImageField(upload_to='enseignants/photos/', blank=True, null=True)
    specialite = models.CharField(max_length=200, help_text="Spécialité du professeur")
    statut = models.CharField(max_length=50, choices=STATUT_CHOICES, default='contractuel')
    corps = models.CharField(max_length=120, blank=True)
    heures_disponibles = models.IntegerField(default=0, help_text="Capacité totale en heures par mois")
    heures_affectees = models.IntegerField(default=0, help_text="Total des heures affectées (calculé automatiquement)")
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name="professeurs")
    date_embauche = models.DateField(blank=True, null=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'professeur'
        verbose_name = "Professeur"
        verbose_name_plural = "Professeurs"
        ordering = ['etablissement', 'nom', 'prenom']
        permissions = [
            ('csv_professeurs', "Peut importer/exporter des données CSV Professeurs"),
        ]
    
    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.specialite}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if not getattr(self, '_photo_syncing', False):
            # Ne synchroniser que si la photo fait partie de l'update
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

    def refresh_heures_depuis_affectations(self, save=True):
        # heures_affectees est une valeur saisie manuellement; elle ne doit pas etre synchronisee automatiquement.
        return

    @property
    def quota_heures(self):
        """Base de capacite utilisee pour les calculs d'affectation."""
        return self.heures_affectees or 0
    
    @property
    def heures_affectees_modules(self):
        """Total des heures reellement affectees via les modules actifs."""
        return sum(a.heures_affectees for a in self.affectations.filter(actif=True))

    @property
    def heures_utilisees(self):
        """Alias explicite metier: heures utilisees dans les modules actifs."""
        return self.heures_affectees_modules

    @property
    def heures_restantes(self):
        """Calcule les heures restantes disponibles."""
        return max((self.heures_affectees or 0) - self.heures_utilisees, 0)
    
    @property
    def taux_utilisation(self):
        """Calcule le taux d'utilisation en pourcentage a partir des affectations reelles."""
        heures_affectees_planifiees = self.heures_affectees or 0
        if heures_affectees_planifiees == 0:
            return 0
        return round((self.heures_utilisees / heures_affectees_planifiees) * 100, 2)

    @property
    def taux_utilisation_width(self):
        """Retourne une largeur de barre valide entre 0 et 100."""
        taux = float(self.taux_utilisation or 0)
        return max(0, min(int(round(taux)), 100))


class Affectation(models.Model):
    """Affecte un professeur à un module"""
    PRIORITE_CHOICES = [
        ('1', 'Critique'),
        ('2', 'Haute'),
        ('3', 'Moyenne'),
        ('4', 'Basse'),
    ]
    
    professeur = models.ForeignKey(Professeur, on_delete=models.CASCADE, related_name="affectations")
    module = models.ForeignKey(Module, on_delete=models.CASCADE, related_name="affectations")
    etablissement = models.ForeignKey(Etablissement, on_delete=models.CASCADE, related_name='affectations', null=True, blank=True)
    filiere = models.ForeignKey(Filiere, on_delete=models.CASCADE, related_name='affectations', null=True, blank=True)
    nombre_heures = models.IntegerField(help_text="Heures assignées au professeur pour ce module")
    heures_affectees = models.IntegerField(default=0, help_text="Heures affectées dans cet établissement")
    priorite = models.CharField(max_length=1, choices=PRIORITE_CHOICES, default='2')
    date_debut = models.DateField()
    date_fin = models.DateField(blank=True, null=True)
    observations = models.TextField(blank=True)
    actif = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'affectation'
        verbose_name = "Affectation"
        verbose_name_plural = "Affectations"
        ordering = ['-priorite', 'professeur', 'module']
        permissions = [
            ('preview_affectation', "Peut prévisualiser une affectation"),
        ]
    
    def __str__(self):
        return f"{self.professeur.prenom} {self.professeur.nom} → {self.module.nom}"

    def clean(self):
        super().clean()

        if self.heures_affectees is None:
            self.heures_affectees = 0

        if self.heures_affectees < 0:
            raise ValidationError("Les heures affectées doivent être positives.")

        if self.date_fin and self.date_fin < self.date_debut:
            raise ValidationError("La date de fin doit être supérieure ou égale à la date de début.")

        if self.filiere_id and self.etablissement_id and not self.filiere.has_etablissement(self.etablissement_id):
            raise ValidationError("La filière sélectionnée n'appartient pas à l'établissement choisi.")

        if self.filiere_id and self.module_id:
            module_dans_filiere = self.module.programmes_principaux.filter(filiere_id=self.filiere_id).exists()
            if not module_dans_filiere:
                raise ValidationError("Le module sélectionné n'est pas rattaché à la filière choisie.")

        affectations_module = Affectation.objects.exclude(pk=self.pk).filter(
            actif=True,
            module_id=self.module_id,
            etablissement_id=self.etablissement_id,
            filiere_id=self.filiere_id,
        )
        heures_module_deja_couvertes = sum(
            affectation.heures_affectees for affectation in affectations_module
        )
        heures_module_total = heures_module_deja_couvertes + self.heures_affectees
        if self.module_id and heures_module_total > self.module.nombre_heures:
            reste_module = max(self.module.nombre_heures - heures_module_deja_couvertes, 0)
            raise ValidationError(
                f"Ce module ne peut plus recevoir que {reste_module}h sur cet établissement et cette filière."
            )

        affectations_prof = Affectation.objects.exclude(pk=self.pk).filter(
            actif=True,
            professeur_id=self.professeur_id,
        )

        if self.professeur_id and self.date_debut:
            conflits_planning = affectations_prof
            if self.date_fin:
                conflits_planning = conflits_planning.filter(
                    date_debut__lte=self.date_fin
                ).filter(
                    Q(date_fin__isnull=True) | Q(date_fin__gte=self.date_debut)
                )
            else:
                conflits_planning = conflits_planning.filter(
                    Q(date_fin__isnull=True) | Q(date_fin__gte=self.date_debut)
                )
            if conflits_planning.exists():
                raise ValidationError(
                    "Le professeur sélectionné est déjà occupé sur cette période."
                )

        heures_prof_deja_affectees = sum(
            affectation.heures_affectees for affectation in affectations_prof
        )
        heures_prof_total = heures_prof_deja_affectees + self.heures_affectees
        if self.professeur_id and heures_prof_total > self.professeur.quota_heures:
            reste_prof = max(self.professeur.quota_heures - heures_prof_deja_affectees, 0)
            raise ValidationError(
                f"Le professeur sélectionné ne dispose plus que de {reste_prof}h disponibles."
            )
    
    def save(self, *args, **kwargs):
        """Met à jour les heures affectées du professeur"""
        if self.heures_affectees == 0 and self.nombre_heures:
            self.heures_affectees = self.nombre_heures
        self.full_clean()
        super().save(*args, **kwargs)
        self.professeur.refresh_heures_depuis_affectations()

    def delete(self, *args, **kwargs):
        professeur = self.professeur
        super().delete(*args, **kwargs)
        professeur.refresh_heures_depuis_affectations()
