from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from config.pagination import AdjustablePaginationMixin
from apps.comptes.permissions import PermissionRequiredMixin
from .models import Formation, Certificat
from .forms import FormationForm, CertificatForm
from apps.agents.models import Agent

# Liste des formations
class FormationListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Formation
    model_permission_model = Formation
    required_action = 'view'
    template_name = 'formations/formation_list.html'
    context_object_name = 'formations'
    paginate_by = 10

    def get_queryset(self):
        queryset = Formation.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(titre__icontains=search) |
                Q(organisme__icontains=search) |
                Q(lieu__icontains=search)
            )
        return queryset.order_by('-id')

# Détail d'une formation
class FormationDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Formation
    model_permission_model = Formation
    required_action = 'view'
    template_name = 'formations/formation_detail.html'
    context_object_name = 'formation'

# Créer une formation
class FormationCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Formation
    model_permission_model = Formation
    form_class = FormationForm
    template_name = 'formations/formation_form.html'
    success_url = reverse_lazy('formation-list')

# Modifier une formation
class FormationUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Formation
    model_permission_model = Formation
    form_class = FormationForm
    template_name = 'formations/formation_form.html'
    success_url = reverse_lazy('formation-list')

# Supprimer une formation
class FormationDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Formation
    model_permission_model = Formation
    template_name = 'formations/formation_confirm_delete.html'
    success_url = reverse_lazy('formation-list')

# Certificats
class CertificatListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Certificat
    model_permission_model = Certificat
    required_action = 'view'
    template_name = 'formations/certificat_list.html'
    context_object_name = 'certificats'
    paginate_by = 10

class CertificatDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Certificat
    model_permission_model = Certificat
    required_action = 'view'
    template_name = 'formations/certificat_detail.html'
    context_object_name = 'certificat'

class CertificatCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Certificat
    model_permission_model = Certificat
    form_class = CertificatForm
    template_name = 'formations/certificat_form.html'
    success_url = reverse_lazy('certificat-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formations'] = Formation.objects.all()
        context['agents'] = Agent.objects.all()
        return context

class CertificatUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Certificat
    model_permission_model = Certificat
    form_class = CertificatForm
    template_name = 'formations/certificat_form.html'
    success_url = reverse_lazy('certificat-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['formations'] = Formation.objects.all()
        context['agents'] = Agent.objects.all()
        return context

class CertificatDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Certificat
    model_permission_model = Certificat
    template_name = 'formations/certificat_confirm_delete.html'
    success_url = reverse_lazy('certificat-list')
