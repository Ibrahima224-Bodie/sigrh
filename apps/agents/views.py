from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.template.loader import render_to_string
from config.pagination import AdjustablePaginationMixin
from apps.comptes.permissions import PermissionRequiredMixin
from .models import Agent
from .forms import AgentForm
from apps.organigramme.models import Structure

# Liste des agents
class AgentListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Agent
    model_permission_model = Agent
    required_action = 'view'
    template_name = 'agents/agent_list.html'
    context_object_name = 'agents'
    paginate_by = 10

    def get_queryset(self):
        queryset = Agent.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(prenom__icontains=search) |
                Q(matricule__icontains=search) |
                Q(fonction__icontains=search)
            )
        return queryset.order_by('matricule')

# Détail d'un agent
class AgentDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Agent
    model_permission_model = Agent
    required_action = 'view'
    template_name = 'agents/agent_detail.html'
    context_object_name = 'agent'

# Créer un agent
class AgentCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Agent
    model_permission_model = Agent
    form_class = AgentForm
    template_name = 'agents/agent_form.html'
    success_url = reverse_lazy('agent-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['structures'] = Structure.objects.all()
        return context
    
    def get_template_names(self):
        if self.request.headers.get('X-Requested-With') == 'fetch':
            return ['agents/agent_form_modal.html']
        return super().get_template_names()
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('X-Requested-With') == 'fetch':
            return JsonResponse({'success': True})
        return response

# Modifier un agent
class AgentUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Agent
    model_permission_model = Agent
    form_class = AgentForm
    template_name = 'agents/agent_form.html'
    success_url = reverse_lazy('agent-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['structures'] = Structure.objects.all()
        return context
    
    def get_template_names(self):
        if self.request.headers.get('X-Requested-With') == 'fetch':
            return ['agents/agent_form_modal.html']
        return super().get_template_names()
    
    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get('X-Requested-With') == 'fetch':
            return JsonResponse({'success': True})
        return response

# Supprimer un agent
class AgentDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Agent
    model_permission_model = Agent
    template_name = 'agents/agent_confirm_delete.html'
    success_url = reverse_lazy('agent-list')

