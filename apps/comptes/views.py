from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, FormView
from django.views.generic import TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import Http404
from django.urls import reverse_lazy
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.models import Permission
from config.pagination import AdjustablePaginationMixin
from .models import User
from .forms import UserForm, UserEditForm, RolePermissionForm, ProfileInfoForm, ProfilePasswordChangeForm
from apps.organigramme.models import Structure
from .permissions import RHAdminRequiredMixin, RolePermissionAdminRequiredMixin, PermissionRequiredMixin, can_toggle_user_activation, get_role_permission_descriptions
from .role_groups import get_role_group
from .permission_labels import get_permission_label_fr


EXCLUDED_PERMISSION_APP_LABELS = ('contenttypes',)

class ProfileView(LoginRequiredMixin, View):
    template_name = 'comptes/profile.html'

    def get(self, request, *args, **kwargs):
        info_form = ProfileInfoForm(instance=request.user)
        password_form = ProfilePasswordChangeForm(user=request.user)
        return render(request, self.template_name, {
            'info_form': info_form,
            'password_form': password_form,
            'active_tab': 'info',
        })

    def post(self, request, *args, **kwargs):
        form_type = request.POST.get('_form_type')
        if form_type == 'info':
            info_form = ProfileInfoForm(request.POST, request.FILES, instance=request.user)
            password_form = ProfilePasswordChangeForm(user=request.user)
            if info_form.is_valid():
                info_form.save()
                messages.success(request, "Vos informations ont été mises à jour avec succès.")
                return redirect('profile')
            active_tab = 'info'
        elif form_type == 'password':
            info_form = ProfileInfoForm(instance=request.user)
            password_form = ProfilePasswordChangeForm(user=request.user, data=request.POST)
            if password_form.is_valid():
                password_form.save()
                update_session_auth_hash(request, password_form.user)
                messages.success(request, "Votre mot de passe a été modifié avec succès.")
                return redirect('profile')
            active_tab = 'password'
        else:
            return redirect('profile')
        return render(request, self.template_name, {
            'info_form': info_form,
            'password_form': password_form,
            'active_tab': active_tab,
        })


class UserListView(LoginRequiredMixin, RHAdminRequiredMixin, AdjustablePaginationMixin, ListView):
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
                Q(role__icontains=search) |
                Q(groups__name__icontains=search) |
                Q(user_permissions__name__icontains=search)
            )
        return queryset.distinct().order_by('-id')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['can_toggle_activation'] = can_toggle_user_activation(self.request.user)
        return context


class UserToggleActiveView(LoginRequiredMixin, RHAdminRequiredMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        if not can_toggle_user_activation(request.user):
            messages.error(request, "Vous n'avez pas la permission d'activer ou desactiver un utilisateur.")
            return redirect('user-list')

        user_to_toggle = get_object_or_404(User, pk=kwargs.get('pk'))
        if user_to_toggle.pk == request.user.pk:
            messages.error(request, "Vous ne pouvez pas desactiver votre propre compte.")
            return redirect('user-list')

        user_to_toggle.is_active = not user_to_toggle.is_active
        user_to_toggle.save(update_fields=['is_active'])

        if user_to_toggle.is_active:
            messages.success(request, f"Le compte {user_to_toggle.username} a ete active.")
        else:
            messages.success(request, f"Le compte {user_to_toggle.username} a ete desactive.")
        return redirect('user-list')

class UserDetailView(LoginRequiredMixin, RHAdminRequiredMixin, DetailView):
    model = User
    template_name = 'comptes/user_detail.html'
    context_object_name = 'user'

class UserCreateView(LoginRequiredMixin, RHAdminRequiredMixin, CreateView):
    model = User
    form_class = UserForm
    template_name = 'comptes/user_form.html'
    success_url = reverse_lazy('user-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['structures'] = Structure.objects.all()
        context['role_choices'] = User.ROLE_CHOICES
        return context

class UserUpdateView(LoginRequiredMixin, RHAdminRequiredMixin, UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'comptes/user_form.html'
    success_url = reverse_lazy('user-list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['structures'] = Structure.objects.all()
        context['role_choices'] = User.ROLE_CHOICES
        return context

class UserDeleteView(LoginRequiredMixin, RHAdminRequiredMixin, DeleteView):
    model = User
    template_name = 'comptes/user_confirm_delete.html'
    success_url = reverse_lazy('user-list')


class RoleListView(LoginRequiredMixin, PermissionRequiredMixin, TemplateView):
    template_name = 'comptes/role_list.html'
    allowed_permissions = ('comptes.manage_role_permissions', 'auth.view_group', 'auth.change_group', 'auth.change_permission')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_counts = {
            item['role']: item['total']
            for item in User.objects.values('role').annotate(total=Count('id'))
        }
        role_rows = []
        for role_code, role_label in User.ROLE_CHOICES:
            role_group = get_role_group(role_code)
            role_rows.append({
                'code': role_code,
                'label': role_label,
                'group_name': role_group.name if role_group else '',
                'user_count': role_counts.get(role_code, 0),
                'permission_descriptions': get_role_permission_descriptions(role_code),
                'users': User.objects.filter(role=role_code).order_by('username')[:8],
            })
        context['role_rows'] = role_rows
        return context


class RolePermissionUpdateView(LoginRequiredMixin, RolePermissionAdminRequiredMixin, FormView):
    template_name = 'comptes/role_permission_form.html'
    form_class = RolePermissionForm
    success_url = reverse_lazy('role-list')

    def dispatch(self, request, *args, **kwargs):
        self.role_code = kwargs['role_code']
        self.role_label = dict(User.ROLE_CHOICES).get(self.role_code)
        if self.role_label is None:
            raise Http404("Role introuvable.")
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['role_code'] = self.role_code
        kwargs['role_label'] = self.role_label
        return kwargs

    def form_valid(self, form):
        form.save()
        messages.success(self.request, f"Les permissions du rôle {self.role_label} ont été mises à jour.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        role_group = get_role_group(self.role_code)
        form = context.get('form')
        context['role_code'] = self.role_code
        context['role_label'] = self.role_label
        context['role_group_name'] = role_group.name
        context['module_fields'] = form.get_module_fields() if form else []
        context['permission_apps'] = form.get_permission_apps() if form else []
        current_permissions = role_group.permissions.select_related('content_type').order_by(
            'content_type__app_label', 'content_type__model', 'name'
        )
        context['current_permissions'] = [
            {
                'id': permission.id,
                'label_fr': get_permission_label_fr(permission),
            }
            for permission in current_permissions
        ]
        context['users'] = User.objects.filter(role=self.role_code).order_by('username')
        return context


class PermissionListView(LoginRequiredMixin, PermissionRequiredMixin, AdjustablePaginationMixin, ListView):
    model = Permission
    template_name = 'comptes/permission_list.html'
    context_object_name = 'permissions'
    paginate_by = 50
    allowed_permissions = ('comptes.manage_role_permissions', 'auth.view_permission', 'auth.change_permission')

    def get_queryset(self):
        queryset = Permission.objects.select_related('content_type').exclude(
            content_type__app_label__in=EXCLUDED_PERMISSION_APP_LABELS
        )
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(codename__icontains=search) |
                Q(content_type__app_label__icontains=search) |
                Q(content_type__model__icontains=search)
            )
        return queryset.order_by('content_type__app_label', 'content_type__model', 'name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('search', '')
        context['permission_rows'] = [
            {
                'permission': permission,
                'label_fr': get_permission_label_fr(permission),
            }
            for permission in context['permissions']
        ]
        return context
