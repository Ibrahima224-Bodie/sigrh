from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Conge
from .forms import CongeForm
from apps.agents.models import Agent

class CongeListView(ListView):
    model = Conge
    template_name = 'absences/conge_list.html'
    context_object_name = 'conges'
    paginate_by = 10

    def get_queryset(self):
        queryset = Conge.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(agent__nom__icontains=search) |
                Q(agent__prenom__icontains=search) |
                Q(type_conge__icontains=search)
            )
        return queryset.order_by('-id')

class CongeDetailView(DetailView):
    model = Conge
    template_name = 'absences/conge_detail.html'
    context_object_name = 'conge'

class CongeCreateView(CreateView):
    model = Conge
    form_class = CongeForm
    template_name = 'absences/conge_form.html'
    success_url = reverse_lazy('conge-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agents'] = Agent.objects.all()
        context['type_conge_choices'] = Conge.TYPE_CONGE
        context['statut_choices'] = [
            ("en_attente", "En attente"),
            ("approuve", "Approuvé"),
            ("refuse", "Refusé"),
        ]
        return context

class CongeUpdateView(UpdateView):
    model = Conge
    form_class = CongeForm
    template_name = 'absences/conge_form.html'
    success_url = reverse_lazy('conge-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agents'] = Agent.objects.all()
        context['type_conge_choices'] = Conge.TYPE_CONGE
        context['statut_choices'] = [
            ("en_attente", "En attente"),
            ("approuve", "Approuvé"),
            ("refuse", "Refusé"),
        ]
        return context

class CongeDeleteView(DeleteView):
    model = Conge
    template_name = 'absences/conge_confirm_delete.html'
    success_url = reverse_lazy('conge-list')
