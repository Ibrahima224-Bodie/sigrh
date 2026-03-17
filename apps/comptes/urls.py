from django.urls import path
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .models import User
from .forms import UserForm, UserEditForm
from django.urls import reverse_lazy

class UserListView(ListView):
    model = User
    template_name = 'comptes/user_list.html'
    context_object_name = 'users'
    paginate_by = 10

class UserDetailView(DetailView):
    model = User
    template_name = 'comptes/user_detail.html'
    context_object_name = 'user'

class UserCreateView(CreateView):
    model = User
    form_class = UserForm
    template_name = 'comptes/user_form.html'
    success_url = reverse_lazy('user-list')

class UserUpdateView(UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'comptes/user_form.html'
    success_url = reverse_lazy('user-list')

class UserDeleteView(DeleteView):
    model = User
    template_name = 'comptes/user_confirm_delete.html'
    success_url = reverse_lazy('user-list')

urlpatterns = [
    path('', UserListView.as_view(), name='user-list'),
    path('create/', UserCreateView.as_view(), name='user-create'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/edit/', UserUpdateView.as_view(), name='user-update'),
    path('<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),
]
