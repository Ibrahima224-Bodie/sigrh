from django.urls import path

from .views import (
    DirectionCreateView,
    DirectionDeleteView,
    DirectionDetailView,
    DirectionListView,
    DirectionUpdateView,
)

urlpatterns = [
    path('', DirectionListView.as_view(), name='direction-list'),
    path('create/', DirectionCreateView.as_view(), name='direction-create'),
    path('<uid:pk>/', DirectionDetailView.as_view(), name='direction-detail'),
    path('<uid:pk>/edit/', DirectionUpdateView.as_view(), name='direction-update'),
    path('<uid:pk>/delete/', DirectionDeleteView.as_view(), name='direction-delete'),
]
