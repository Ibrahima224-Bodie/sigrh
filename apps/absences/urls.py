from django.urls import path
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Conge
from .forms import CongeForm
from django.urls import reverse_lazy

class CongeListView(ListView):
    model = Conge
    template_name = 'absences/conge_list.html'
    context_object_name = 'conges'
    paginate_by = 10

class CongeDetailView(DetailView):
    model = Conge
    template_name = 'absences/conge_detail.html'
    context_object_name = 'conge'

class CongeCreateView(CreateView):
    model = Conge
    form_class = CongeForm
    template_name = 'absences/conge_form.html'
    success_url = reverse_lazy('conge-list')

class CongeUpdateView(UpdateView):
    model = Conge
    form_class = CongeForm
    template_name = 'absences/conge_form.html'
    success_url = reverse_lazy('conge-list')

class CongeDeleteView(DeleteView):
    model = Conge
    template_name = 'absences/conge_confirm_delete.html'
    success_url = reverse_lazy('conge-list')

urlpatterns = [
    path('', CongeListView.as_view(), name='conge-list'),
    path('create/', CongeCreateView.as_view(), name='conge-create'),
    path('<int:pk>/', CongeDetailView.as_view(), name='conge-detail'),
    path('<int:pk>/edit/', CongeUpdateView.as_view(), name='conge-update'),
    path('<int:pk>/delete/', CongeDeleteView.as_view(), name='conge-delete'),
]
