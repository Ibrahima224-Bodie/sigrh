from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import Direction
from .forms import DirectionForm

class DirectionListView(ListView):
    model = Direction
    template_name = 'directions/direction_list.html'
    context_object_name = 'directions'
    paginate_by = 10

    def get_queryset(self):
        queryset = Direction.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(nom__icontains=search) |
                Q(sigle__icontains=search)
            )
        return queryset.order_by('-id')

class DirectionDetailView(DetailView):
    model = Direction
    template_name = 'directions/direction_detail.html'
    context_object_name = 'direction'

class DirectionCreateView(CreateView):
    model = Direction
    form_class = DirectionForm
    template_name = 'directions/direction_form.html'
    success_url = reverse_lazy('direction-list')

class DirectionUpdateView(UpdateView):
    model = Direction
    form_class = DirectionForm
    template_name = 'directions/direction_form.html'
    success_url = reverse_lazy('direction-list')

class DirectionDeleteView(DeleteView):
    model = Direction
    template_name = 'directions/direction_confirm_delete.html'
    success_url = reverse_lazy('direction-list')
