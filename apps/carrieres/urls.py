from django.urls import path
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Carriere
from .forms import CarriereForm
from django.urls import reverse_lazy

class CarriereListView(ListView):
    model = Carriere
    template_name = 'carrieres/carriere_list.html'
    context_object_name = 'carrieres'
    paginate_by = 10

class CarriereDetailView(DetailView):
    model = Carriere
    template_name = 'carrieres/carriere_detail.html'
    context_object_name = 'carriere'

class CarriereCreateView(CreateView):
    model = Carriere
    form_class = CarriereForm
    template_name = 'carrieres/carriere_form.html'
    success_url = reverse_lazy('carriere-list')

class CarriereUpdateView(UpdateView):
    model = Carriere
    form_class = CarriereForm
    template_name = 'carrieres/carriere_form.html'
    success_url = reverse_lazy('carriere-list')

class CarriereDeleteView(DeleteView):
    model = Carriere
    template_name = 'carrieres/carriere_confirm_delete.html'
    success_url = reverse_lazy('carriere-list')

urlpatterns = [
    path('', CarriereListView.as_view(), name='carriere-list'),
    path('create/', CarriereCreateView.as_view(), name='carriere-create'),
    path('<int:pk>/', CarriereDetailView.as_view(), name='carriere-detail'),
    path('<int:pk>/edit/', CarriereUpdateView.as_view(), name='carriere-update'),
    path('<int:pk>/delete/', CarriereDeleteView.as_view(), name='carriere-delete'),
]
