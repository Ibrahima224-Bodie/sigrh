from django.urls import path

from .views import (
    StructureCreateView,
    StructureDeleteView,
    StructureDetailView,
    StructureListView,
    StructureUpdateView,
)

urlpatterns = [
    path('', StructureListView.as_view(), name='structure-list'),
    path('create/', StructureCreateView.as_view(), name='structure-create'),
    path('<uid:pk>/', StructureDetailView.as_view(), name='structure-detail'),
    path('<uid:pk>/edit/', StructureUpdateView.as_view(), name='structure-update'),
    path('<uid:pk>/delete/', StructureDeleteView.as_view(), name='structure-delete'),
]
