from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Carriere
from .forms import CarriereForm
from apps.agents.models import Agent

class CarriereListView(ListView):
    model = Carriere
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

class CarriereDetailView(DetailView):
    model = Carriere
    template_name = 'carrieres/carriere_detail.html'
    context_object_name = 'carriere'

class CarriereCreateView(CreateView):
    model = Carriere
    form_class = CarriereForm
    template_name = 'carrieres/carriere_form.html'
    success_url = reverse_lazy('carriere-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agents'] = Agent.objects.all()
        return context

class CarriereUpdateView(UpdateView):
    model = Carriere
    form_class = CarriereForm
    template_name = 'carrieres/carriere_form.html'
    success_url = reverse_lazy('carriere-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['agents'] = Agent.objects.all()
        return context

class CarriereDeleteView(DeleteView):
    model = Carriere
    template_name = 'carrieres/carriere_confirm_delete.html'
    success_url = reverse_lazy('carriere-list')
