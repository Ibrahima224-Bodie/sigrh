from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.db.models import Q
from config.pagination import AdjustablePaginationMixin
from apps.comptes.permissions import PermissionRequiredMixin
from .models import Structure
from .forms import StructureForm

class StructureListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Structure
    model_permission_model = Structure
    required_action = 'view'
    template_name = 'organigramme/structure_list.html'
    context_object_name = 'structures'
    paginate_by = 10

    def get_queryset(self):
        queryset = Structure.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(sigle__icontains=search) |
                Q(type_structure__icontains=search)
            )
        return queryset.order_by('-id')

class StructureDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = Structure
    model_permission_model = Structure
    required_action = 'view'
    template_name = 'organigramme/structure_detail.html'
    context_object_name = 'structure'

class StructureCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Structure
    model_permission_model = Structure
    form_class = StructureForm
    template_name = 'organigramme/structure_form.html'
    success_url = reverse_lazy('structure-list')

class StructureUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Structure
    model_permission_model = Structure
    form_class = StructureForm
    template_name = 'organigramme/structure_form.html'
    success_url = reverse_lazy('structure-list')

class StructureDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Structure
    model_permission_model = Structure
    template_name = 'organigramme/structure_confirm_delete.html'
    success_url = reverse_lazy('structure-list')
