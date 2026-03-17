from django.urls import path
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Structure
from .forms import StructureForm
from django.urls import reverse_lazy

class StructureListView(ListView):
    model = Structure
    template_name = 'organigramme/structure_list.html'
    context_object_name = 'structures'
    paginate_by = 10

class StructureDetailView(DetailView):
    model = Structure
    template_name = 'organigramme/structure_detail.html'
    context_object_name = 'structure'

class StructureCreateView(CreateView):
    model = Structure
    form_class = StructureForm
    template_name = 'organigramme/structure_form.html'
    success_url = reverse_lazy('structure-list')

class StructureUpdateView(UpdateView):
    model = Structure
    form_class = StructureForm
    template_name = 'organigramme/structure_form.html'
    success_url = reverse_lazy('structure-list')

class StructureDeleteView(DeleteView):
    model = Structure
    template_name = 'organigramme/structure_confirm_delete.html'
    success_url = reverse_lazy('structure-list')

urlpatterns = [
    path('', StructureListView.as_view(), name='structure-list'),
    path('create/', StructureCreateView.as_view(), name='structure-create'),
    path('<int:pk>/', StructureDetailView.as_view(), name='structure-detail'),
    path('<int:pk>/edit/', StructureUpdateView.as_view(), name='structure-update'),
    path('<int:pk>/delete/', StructureDeleteView.as_view(), name='structure-delete'),
]
