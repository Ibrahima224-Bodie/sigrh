from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from config.pagination import AdjustablePaginationMixin
from apps.comptes.permissions import PermissionRequiredMixin
from .models import Carriere
from .forms import CarriereForm
from apps.agents.models import Agent

class CarriereListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Carriere
    model_permission_model = Carriere
    required_action = 'view'
    template_name = 'carrieres/carriere_list.html'
    context_object_name = 'carrieres'
    paginate_by = 10

    def get_queryset(self):
        queryset = Carriere.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(agent__nom__icontains=search) |
                Q(agent__prenom__icontains=search) |
                Q(poste__icontains=search) |
                Q(grade__icontains=search)
            )
        return queryset.order_by('-id')

class CarriereDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Carriere
    model_permission_model = Carriere
    required_action = 'view'
    template_name = 'carrieres/carriere_detail.html'
    context_object_name = 'carriere'

class CarriereCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Carriere
    model_permission_model = Carriere
    form_class = CarriereForm
    template_name = 'carrieres/carriere_form.html'
    success_url = reverse_lazy('carriere-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agents'] = Agent.objects.all()
        return context

class CarriereUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Carriere
    model_permission_model = Carriere
    form_class = CarriereForm
    template_name = 'carrieres/carriere_form.html'
    success_url = reverse_lazy('carriere-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agents'] = Agent.objects.all()
        return context

class CarriereDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Carriere
    model_permission_model = Carriere
    template_name = 'carrieres/carriere_confirm_delete.html'
    success_url = reverse_lazy('carriere-list')
