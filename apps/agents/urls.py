from django.urls import path
from .views import (
    AgentListView, AgentDetailView, AgentCreateView, 
    AgentUpdateView, AgentDeleteView
)

urlpatterns = [
    path('', AgentListView.as_view(), name='agent-list'),
    path('create/', AgentCreateView.as_view(), name='agent-create'),
    path('<int:pk>/', AgentDetailView.as_view(), name='agent-detail'),
    path('<int:pk>/edit/', AgentUpdateView.as_view(), name='agent-update'),
    path('<int:pk>/delete/', AgentDeleteView.as_view(), name='agent-delete'),
]
