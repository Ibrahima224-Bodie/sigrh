from django.urls import path
from . import views

app_name = 'enseignants'

urlpatterns = [
    # Referentiels administration
    path('regions/', views.RegionListView.as_view(), name='region_list'),
    path('regions/create/', views.RegionCreateView.as_view(), name='region_create'),
    path('regions/<uid:pk>/update/', views.RegionUpdateView.as_view(), name='region_update'),
    path('regions/<uid:pk>/delete/', views.RegionDeleteView.as_view(), name='region_delete'),

    path('prefectures/', views.PrefectureListView.as_view(), name='prefecture_list'),
    path('prefectures/create/', views.PrefectureCreateView.as_view(), name='prefecture_create'),
    path('prefectures/<uid:pk>/update/', views.PrefectureUpdateView.as_view(), name='prefecture_update'),
    path('prefectures/<uid:pk>/delete/', views.PrefectureDeleteView.as_view(), name='prefecture_delete'),

    path('communes/', views.CommuneListView.as_view(), name='commune_list'),
    path('communes/create/', views.CommuneCreateView.as_view(), name='commune_create'),
    path('communes/<uid:pk>/update/', views.CommuneUpdateView.as_view(), name='commune_update'),
    path('communes/<uid:pk>/delete/', views.CommuneDeleteView.as_view(), name='commune_delete'),

    path('quartiers/', views.QuartierListView.as_view(), name='quartier_list'),
    path('quartiers/create/', views.QuartierCreateView.as_view(), name='quartier_create'),
    path('quartiers/<uid:pk>/update/', views.QuartierUpdateView.as_view(), name='quartier_update'),
    path('quartiers/<uid:pk>/delete/', views.QuartierDeleteView.as_view(), name='quartier_delete'),

    path('secteurs/', views.SecteurListView.as_view(), name='secteur_list'),
    path('secteurs/create/', views.SecteurCreateView.as_view(), name='secteur_create'),
    path('secteurs/<uid:pk>/update/', views.SecteurUpdateView.as_view(), name='secteur_update'),
    path('secteurs/<uid:pk>/delete/', views.SecteurDeleteView.as_view(), name='secteur_delete'),

    path('csv/<str:entity>/template/', views.export_csv_template, name='export_csv_template'),
    path('csv/<str:entity>/export/', views.export_csv_data, name='export_csv_data'),
    path('csv/<str:entity>/import/', views.import_csv_data, name='import_csv_data'),

    # API de filtrage geographique (Region -> Prefecture -> Commune -> Quartier -> Secteur)
    path('api/prefectures/', views.ajax_prefectures, name='ajax-prefectures'),
    path('api/communes/', views.ajax_communes, name='ajax-communes'),
    path('api/quartiers/', views.ajax_quartiers, name='ajax-quartiers'),
    path('api/secteurs/', views.ajax_secteurs, name='ajax-secteurs'),
    path('api/filieres-by-etablissement/', views.ajax_filieres_by_etablissement, name='ajax-filieres-by-etablissement'),
    path('api/programmes-by-filiere/', views.ajax_programmes_by_filiere, name='ajax-programmes-by-filiere'),
    path('api/modules-by-filiere/', views.ajax_modules_by_filiere, name='ajax-modules-by-filiere'),
    path('api/affectation-preview/', views.ajax_affectation_preview, name='ajax-affectation-preview'),

    # Alias de compatibilite
    path('csv/<str:entity>/template/', views.export_csv_template, name='csv_template'),
    path('csv/<str:entity>/export/', views.export_csv_data, name='csv_export'),
    path('csv/<str:entity>/import/', views.import_csv_data, name='csv_import'),

    # Etablissement URLs
    path('etablissements/', views.EtablissementListView.as_view(), name='etablissement_list'),
    path('etablissements/<uid:pk>/', views.EtablissementDetailView.as_view(), name='etablissement_detail'),
    path('etablissements/create/', views.EtablissementCreateView.as_view(), name='etablissement_create'),
    path('etablissements/<uid:pk>/update/', views.EtablissementUpdateView.as_view(), name='etablissement_update'),
    path('etablissements/<uid:pk>/delete/', views.EtablissementDeleteView.as_view(), name='etablissement_delete'),
    
    # Filiere URLs
    path('filieres/', views.FiliereListView.as_view(), name='filiere_list'),
    path('filieres/<uid:pk>/', views.FiliereDetailView.as_view(), name='filiere_detail'),
    path('filieres/create/', views.FiliereCreateView.as_view(), name='filiere_create'),
    path('filieres/<uid:pk>/update/', views.FiliereUpdateView.as_view(), name='filiere_update'),
    path('filieres/<uid:pk>/delete/', views.FiliereDeleteView.as_view(), name='filiere_delete'),
    
    # Programme URLs
    path('programmes/', views.ProgrammeListView.as_view(), name='programme_list'),
    path('programmes/create/', views.ProgrammeCreateView.as_view(), name='programme_create'),
    path('programmes/<uid:pk>/', views.ProgrammeDetailView.as_view(), name='programme_detail'),
    path('programmes/<uid:pk>/update/', views.ProgrammeUpdateView.as_view(), name='programme_update'),
    path('programmes/<uid:pk>/delete/', views.ProgrammeDeleteView.as_view(), name='programme_delete'),
    
    # Module URLs
    path('modules/', views.ModuleListView.as_view(), name='module_list'),
    path('modules/create/', views.ModuleCreateView.as_view(), name='module_create'),
    path('modules/<uid:pk>/', views.ModuleDetailView.as_view(), name='module_detail'),
    path('modules/<uid:pk>/update/', views.ModuleUpdateView.as_view(), name='module_update'),
    path('modules/<uid:pk>/delete/', views.ModuleDeleteView.as_view(), name='module_delete'),
    
    # Professeur URLs
    path('professeurs/', views.ProfesseurListView.as_view(), name='professeur_list'),
    path('professeurs/<uid:pk>/', views.ProfesseurDetailView.as_view(), name='professeur_detail'),
    path('professeurs/create/', views.ProfesseurCreateView.as_view(), name='professeur_create'),
    path('professeurs/<uid:pk>/update/', views.ProfesseurUpdateView.as_view(), name='professeur_update'),
    path('professeurs/<uid:pk>/delete/', views.ProfesseurDeleteView.as_view(), name='professeur_delete'),
    
    # Affectation URLs
    path('affectations/', views.AffectationListView.as_view(), name='affectation_list'),
    path('affectations/<uid:pk>/', views.AffectationDetailView.as_view(), name='affectation_detail'),
    path('affectations/create/', views.AffectationCreateView.as_view(), name='affectation_create'),
    path('affectations/<uid:pk>/update/', views.AffectationUpdateView.as_view(), name='affectation_update'),
    path('affectations/<uid:pk>/delete/', views.AffectationDeleteView.as_view(), name='affectation_delete'),

    # Besoins URLs
    path('besoins/', views.BesoinListView.as_view(), name='besoin_list'),
    path('besoins/<uid:module_id>/suggestions/', views.BesoinSuggestionsView.as_view(), name='besoin_suggestions'),
]
