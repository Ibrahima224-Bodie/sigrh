from functools import wraps

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from django.views.generic.edit import CreateView, DeleteView, UpdateView

from .permission_labels import get_permission_label_fr
from .role_groups import get_role_group


CONGE_REQUEST_PERMISSION = "absences.demander_conge"
CONGE_DIRECTEUR_APPROVAL_PERMISSION = "absences.approuver_conge_directeur"
CONGE_DRH_VALIDATION_PERMISSION = "absences.valider_conge_drh"


def _format_permission_label(permission):
    return get_permission_label_fr(permission)


def user_has_any_permission(user, permissions):
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return any(user.has_perm(permission) for permission in permissions)


def get_model_permission_codename(model, action):
    return f"{model._meta.app_label}.{action}_{model._meta.model_name}"


def user_has_model_permission(user, model, action):
    return user_has_any_permission(user, [get_model_permission_codename(model, action)])


def user_has_any_model_permission(user, model, actions):
    permissions = [get_model_permission_codename(model, action) for action in actions]
    return user_has_any_permission(user, permissions)


def can_toggle_user_activation(user):
    return user_has_any_permission(user, ["comptes.toggle_user_activation"])


def get_role_permission_descriptions(role_code):
    role_group = get_role_group(role_code)
    if role_group is None:
        return []
    permissions = role_group.permissions.select_related("content_type").order_by(
        "content_type__app_label", "content_type__model", "name"
    )
    return [_format_permission_label(permission) for permission in permissions]


def can_manage_role_permissions(user):
    return user_has_any_permission(user, ["comptes.manage_role_permissions", "auth.change_group", "auth.change_permission"])


def can_manage_user_administration(user):
    return can_manage_role_permissions(user) or user_has_any_permission(
        user,
        [
            "comptes.view_user",
            "comptes.add_user",
            "comptes.change_user",
            "comptes.delete_user",
        ],
    )


def _user_has_role(user, roles):
    return user.is_authenticated and (user.is_superuser or getattr(user, "role", None) in roles)


def user_can_request_conge(user):
    return user_has_any_permission(user, [CONGE_REQUEST_PERMISSION])


def user_can_approve_conge_directeur(user):
    return user_has_any_permission(user, [CONGE_DIRECTEUR_APPROVAL_PERMISSION])


def user_can_validate_conge_drh(user):
    return user_has_any_permission(user, [CONGE_DRH_VALIDATION_PERMISSION])


def _infer_required_action(view):
    if isinstance(view, CreateView):
        return "add"
    if isinstance(view, UpdateView):
        return "change"
    if isinstance(view, DeleteView):
        return "delete"
    return getattr(view, "required_action", None)


class PermissionRequiredMixin(UserPassesTestMixin):
    allowed_permissions = ()
    model_permission_model = None
    required_action = None
    permission_denied_message = "Vous n'avez pas la permission d'acceder a cette page."

    def get_allowed_permissions(self):
        permissions = list(self.allowed_permissions)
        model = self.model_permission_model or getattr(self, "model", None)
        action = self.required_action or _infer_required_action(self)
        if model is not None and action:
            permissions.append(get_model_permission_codename(model, action))
        return tuple(dict.fromkeys(permission for permission in permissions if permission))

    def test_func(self):
        return user_has_any_permission(self.request.user, self.get_allowed_permissions())

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, self.permission_denied_message)
            return redirect("dashboard")
        return super().handle_no_permission()


class CongeRequestMixin(UserPassesTestMixin):
    def test_func(self):
        return user_can_request_conge(self.request.user)
    
    def handle_no_permission(self):
        messages.error(self.request, "Vous n'avez pas la permission de demander un congé.")
        return redirect("conge-list")


class RoleRequiredMixin(UserPassesTestMixin):
    allowed_roles = ()
    permission_denied_message = "Vous n'avez pas la permission d'acceder a cette page."

    def test_func(self):
        return _user_has_role(self.request.user, self.allowed_roles)

    def handle_no_permission(self):
        if self.request.user.is_authenticated:
            messages.error(self.request, self.permission_denied_message)
            return redirect("dashboard")
        return super().handle_no_permission()


class RHAdminRequiredMixin(PermissionRequiredMixin):
    def test_func(self):
        return can_manage_user_administration(self.request.user)


class RolePermissionAdminRequiredMixin(PermissionRequiredMixin):
    def test_func(self):
        return can_manage_role_permissions(self.request.user)


class EnseignantsWriteRequiredMixin(PermissionRequiredMixin):
    permission_denied_message = "Vous n'avez pas la permission de modifier ce référentiel."


def any_permission_required(*permissions):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not user_has_any_permission(request.user, permissions):
                messages.error(request, "Vous n'avez pas la permission d'effectuer cette action.")
                return redirect("dashboard")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator


def model_permissions_required(model, *actions):
    permissions = [get_model_permission_codename(model, action) for action in actions]
    return any_permission_required(*permissions)


def role_required(*roles):
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped(request, *args, **kwargs):
            if not _user_has_role(request.user, roles):
                messages.error(request, "Vous n'avez pas la permission d'effectuer cette action.")
                return redirect("dashboard")
            return view_func(request, *args, **kwargs)

        return _wrapped

    return decorator
