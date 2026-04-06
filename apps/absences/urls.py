from django.urls import path
from . import views

urlpatterns = [
    path('', views.CongeListView.as_view(), name='conge-list'),
    path('create/', views.CongeCreateView.as_view(), name='conge-create'),
    path('<uid:pk>/', views.CongeDetailView.as_view(), name='conge-detail'),
    path('<uid:pk>/edit/', views.CongeUpdateView.as_view(), name='conge-update'),
    path('<uid:pk>/delete/', views.CongeDeleteView.as_view(), name='conge-delete'),
    path('<uid:pk>/approuver-directeur/', views.ApprobationDirecteurView.as_view(), name='conge-approuver-directeur'),
    path('<uid:pk>/valider-drh/', views.ValidationDRHView.as_view(), name='conge-valider-drh'),
    path('<uid:pk>/commentaire/', views.AjouterCommentaireView.as_view(), name='conge-ajouter-commentaire'),
]
