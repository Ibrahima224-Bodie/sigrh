from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Structure
from .forms import StructureForm

class StructureListView(ListView):
    model = Structure
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
