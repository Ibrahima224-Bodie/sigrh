from django.urls import path

from .views import (
    CarriereCreateView,
    CarriereDeleteView,
    CarriereDetailView,
    CarriereListView,
    CarriereUpdateView,
)

urlpatterns = [
    path('', CarriereListView.as_view(), name='carriere-list'),
    path('create/', CarriereCreateView.as_view(), name='carriere-create'),
    path('<uid:pk>/', CarriereDetailView.as_view(), name='carriere-detail'),
    path('<uid:pk>/edit/', CarriereUpdateView.as_view(), name='carriere-update'),
    path('<uid:pk>/delete/', CarriereDeleteView.as_view(), name='carriere-delete'),
]
