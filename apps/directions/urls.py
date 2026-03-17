from django.urls import path
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Direction
from .forms import DirectionForm
from django.urls import reverse_lazy

class DirectionListView(ListView):
    model = Direction
    template_name = 'directions/direction_list.html'
    context_object_name = 'directions'
    paginate_by = 10

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

urlpatterns = [
    path('', DirectionListView.as_view(), name='direction-list'),
    path('create/', DirectionCreateView.as_view(), name='direction-create'),
    path('<int:pk>/', DirectionDetailView.as_view(), name='direction-detail'),
    path('<int:pk>/edit/', DirectionUpdateView.as_view(), name='direction-update'),
    path('<int:pk>/delete/', DirectionDeleteView.as_view(), name='direction-delete'),
]
