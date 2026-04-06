from django.urls import path

from .views import (
    CertificatCreateView,
    CertificatDeleteView,
    CertificatDetailView,
    CertificatListView,
    CertificatUpdateView,
    FormationCreateView,
    FormationDeleteView,
    FormationDetailView,
    FormationListView,
    FormationUpdateView,
)

urlpatterns = [
    path('', FormationListView.as_view(), name='formation-list'),
    path('create/', FormationCreateView.as_view(), name='formation-create'),
    path('<uid:pk>/', FormationDetailView.as_view(), name='formation-detail'),
    path('<uid:pk>/edit/', FormationUpdateView.as_view(), name='formation-update'),
    path('<uid:pk>/delete/', FormationDeleteView.as_view(), name='formation-delete'),
    path('certificats/', CertificatListView.as_view(), name='certificat-list'),
    path('certificats/create/', CertificatCreateView.as_view(), name='certificat-create'),
    path('certificats/<uid:pk>/', CertificatDetailView.as_view(), name='certificat-detail'),
    path('certificats/<uid:pk>/edit/', CertificatUpdateView.as_view(), name='certificat-update'),
    path('certificats/<uid:pk>/delete/', CertificatDeleteView.as_view(), name='certificat-delete'),
]
