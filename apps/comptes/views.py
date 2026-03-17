from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from .models import User
from .forms import UserForm, UserEditForm
from apps.organigramme.models import Structure

class UserListView(ListView):
    model = User
    template_name = 'comptes/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

    def get_queryset(self):
        queryset = User.objects.all()
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search) |
                Q(role__icontains=search)
            )
        return queryset.order_by('-id')

class UserDetailView(DetailView):
    model = User
    template_name = 'comptes/user_detail.html'
    context_object_name = 'user'

class UserCreateView(CreateView):
    model = User
    form_class = UserForm
    template_name = 'comptes/user_form.html'
    success_url = reverse_lazy('user-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['structures'] = Structure.objects.all()
        context['role_choices'] = User.ROLE_CHOICES
        return context

class UserUpdateView(UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'comptes/user_form.html'
    success_url = reverse_lazy('user-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['structures'] = Structure.objects.all()
        context['role_choices'] = User.ROLE_CHOICES
        return context

class UserDeleteView(DeleteView):
    model = User
    template_name = 'comptes/user_confirm_delete.html'
    success_url = reverse_lazy('user-list')
