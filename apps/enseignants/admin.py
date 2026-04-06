from django.contrib import admin
from .models import (
    Etablissement,
    Filiere,
    Programme,
    Module,
    Professeur,
    Affectation,
    Region,
    Prefecture,
    Commune,
    Quartier,
    Secteur,
)


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom')
    search_fields = ('nom',)


@admin.register(Prefecture)
class PrefectureAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'region')
    list_filter = ('region',)
    search_fields = ('nom', 'region__nom')


@admin.register(Commune)
class CommuneAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'prefecture')
    list_filter = ('prefecture__region', 'prefecture')
    search_fields = ('nom', 'prefecture__nom')


@admin.register(Quartier)
class QuartierAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'commune')
    list_filter = ('commune__prefecture',)
    search_fields = ('nom', 'commune__nom')


@admin.register(Secteur)
class SecteurAdmin(admin.ModelAdmin):
    list_display = ('id', 'nom', 'quartier')
    list_filter = ('quartier__commune',)
    search_fields = ('nom', 'quartier__nom')

@admin.register(Etablissement)
class EtablissementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'region', 'prefecture', 'commune', 'quartier', 'secteur')
    list_filter = ('region', 'prefecture', 'commune', 'date_creation')
    search_fields = ('nom', 'code', 'email')
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'code', 'localisation')
        }),
        ('Contact', {
            'fields': ('contact', 'email', 'directeur')
        }),
        ('Dates', {
            'fields': ('date_creation',)
        }),
        ('Zones géographiques', {
            'fields': ('region', 'prefecture', 'commune', 'quartier', 'secteur')
        }),
    )


@admin.register(Filiere)
class FiliereAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'programme', 'etablissement', 'duree_mois', 'nombre_heures_total')
    list_filter = ('etablissement', 'date_creation')
    search_fields = ('nom', 'code', 'description')
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'code', 'programme', 'etablissement')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Détails', {
            'fields': ('duree_mois', 'nombre_heures_total')
        }),
        ('Dates', {
            'fields': ('date_creation',)
        }),
    )


@admin.register(Programme)
class ProgrammeAdmin(admin.ModelAdmin):
    list_display = ('nom', 'filiere', 'modules_formation_list', 'semestre', 'nombre_heures', 'ordre')
    list_filter = ('filiere', 'semestre')
    search_fields = ('nom', 'code')
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'code', 'filiere', 'module_formation')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Détails', {
            'fields': ('semestre', 'nombre_heures', 'ordre')
        }),
    )

    def modules_formation_list(self, obj):
        return ', '.join(obj.module_formation.values_list('nom', flat=True))

    modules_formation_list.short_description = 'Modules formation'


@admin.register(Module)
class ModuleAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'nombre_heures', 'ordre')
    list_filter = ()
    search_fields = ('nom', 'code', 'description')
    fieldsets = (
        ('Informations de base', {
            'fields': ('nom', 'code')
        }),
        ('Description', {
            'fields': ('description',)
        }),
        ('Détails pédagogiques', {
            'fields': ('nombre_heures', 'ordre')
        }),
    )


@admin.register(Professeur)
class ProfesseurAdmin(admin.ModelAdmin):
    list_display = ('matricule', 'nom', 'prenom', 'sexe', 'hierarchie', 'specialite', 'statut', 'corps', 'etablissement')
    list_filter = ('etablissement', 'statut', 'actif', 'date_embauche')
    search_fields = ('matricule', 'nom', 'prenom', 'email', 'specialite')
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('matricule', 'prenom', 'nom', 'sexe', 'email', 'telephone')
        }),
        ('Professionnel', {
            'fields': ('hierarchie', 'specialite', 'statut', 'corps', 'etablissement')
        }),
        ('Heures', {
            'fields': ('heures_affectees',)
        }),
        ('Dates', {
            'fields': ('date_embauche', 'actif')
        }),
    )


@admin.register(Affectation)
class AffectationAdmin(admin.ModelAdmin):
    list_display = ('id', 'professeur', 'etablissement', 'filiere', 'module', 'heures_affectees', 'priorite', 'date_debut', 'actif')
    list_filter = ('professeur__etablissement', 'priorite', 'actif', 'date_debut')
    search_fields = ('professeur__nom', 'professeur__prenom', 'module__nom')
    fieldsets = (
        ('Affectation', {
            'fields': ('professeur', 'etablissement', 'filiere', 'module')
        }),
        ('Détails', {
            'fields': ('nombre_heures', 'heures_affectees', 'priorite', 'observations')
        }),
        ('Dates', {
            'fields': ('date_debut', 'date_fin')
        }),
        ('Statut', {
            'fields': ('actif',)
        }),
    )
