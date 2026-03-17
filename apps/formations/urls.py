from django.urls import path
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import Formation, Certificat
from .forms import FormationForm, CertificatForm
from django.urls import reverse_lazy

class FormationListView(ListView):
    model = Formation
    template_name = 'formations/formation_list.html'
    context_object_name = 'formations'
    paginate_by = 10

class FormationDetailView(DetailView):
    model = Formation
    template_name = 'formations/formation_detail.html'
    context_object_name = 'formation'

class FormationCreateView(CreateView):
    model = Formation
    form_class = FormationForm
    template_name = 'formations/formation_form.html'
    success_url = reverse_lazy('formation-list')

class FormationUpdateView(UpdateView):
    model = Formation
    form_class = FormationForm
    template_name = 'formations/formation_form.html'
    success_url = reverse_lazy('formation-list')

class FormationDeleteView(DeleteView):
    model = Formation
    template_name = 'formations/formation_confirm_delete.html'
    success_url = reverse_lazy('formation-list')

class CertificatListView(ListView):
    model = Certificat
    template_name = 'formations/certificat_list.html'
    context_object_name = 'certificats'
    paginate_by = 10

class CertificatDetailView(DetailView):
    model = Certificat
    template_name = 'formations/certificat_detail.html'
    context_object_name = 'certificat'

class CertificatCreateView(CreateView):
    model = Certificat
    form_class = CertificatForm
    template_name = 'formations/certificat_form.html'
    success_url = reverse_lazy('certificat-list')

class CertificatUpdateView(UpdateView):
    model = Certificat
    form_class = CertificatForm
    template_name = 'formations/certificat_form.html'
    success_url = reverse_lazy('certificat-list')

class CertificatDeleteView(DeleteView):
    model = Certificat
    template_name = 'formations/certificat_confirm_delete.html'
    success_url = reverse_lazy('certificat-list')

urlpatterns = [
    path('', FormationListView.as_view(), name='formation-list'),
    path('create/', FormationCreateView.as_view(), name='formation-create'),
    path('<int:pk>/', FormationDetailView.as_view(), name='formation-detail'),
    path('<int:pk>/edit/', FormationUpdateView.as_view(), name='formation-update'),
    path('<int:pk>/delete/', FormationDeleteView.as_view(), name='formation-delete'),
    path('certificats/', CertificatListView.as_view(), name='certificat-list'),
    path('certificats/create/', CertificatCreateView.as_view(), name='certificat-create'),
    path('certificats/<int:pk>/', CertificatDetailView.as_view(), name='certificat-detail'),
    path('certificats/<int:pk>/edit/', CertificatUpdateView.as_view(), name='certificat-update'),
    path('certificats/<int:pk>/delete/', CertificatDeleteView.as_view(), name='certificat-delete'),
]
