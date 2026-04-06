from django.urls import path
from .views import (
    AgentListView, AgentDetailView, AgentCreateView, 
    AgentUpdateView, AgentDeleteView
)

urlpatterns = [
    path('', AgentListView.as_view(), name='agent-list'),
    path('create/', AgentCreateView.as_view(), name='agent-create'),
    path('<uid:pk>/', AgentDetailView.as_view(), name='agent-detail'),
    path('<uid:pk>/edit/', AgentUpdateView.as_view(), name='agent-update'),
    path('<uid:pk>/delete/', AgentDeleteView.as_view(), name='agent-delete'),
]
