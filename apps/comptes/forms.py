from django import forms
from django.apps import apps as django_apps
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, PasswordChangeForm
from .models import User
from apps.organigramme.models import Structure
from .role_groups import get_manual_groups_queryset, get_role_group, sync_user_role_group
from .permission_labels import get_permission_label_fr


EXCLUDED_PERMISSION_APP_LABELS = ('contenttypes',)


class FrenchPermissionMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self, obj):
        return get_permission_label_fr(obj)


class ProfileInfoForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'photo')
        labels = {
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'email': 'Email',
            'photo': 'Photo de profil',
        }
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }


class ProfilePasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Mot de passe actuel'})
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Nouveau mot de passe'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Confirmer le nouveau mot de passe'})
        self.fields['old_password'].label = 'Mot de passe actuel'
        self.fields['new_password1'].label = 'Nouveau mot de passe'
        self.fields['new_password2'].label = 'Confirmer le nouveau mot de passe'


class RolePermissionForm(forms.Form):
    FIELD_PREFIX = 'permission__'
    ACTION_ORDER = ('view', 'add', 'change', 'delete')

    def __init__(self, *args, role_code=None, role_label=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.role_code = role_code
        self.role_label = role_label
        self.role_group = get_role_group(role_code)
        self._permission_field_names = []
        self._permission_apps = []

        current_permission_ids = set()
        if self.role_group is not None:
            current_permission_ids = set(self.role_group.permissions.values_list('id', flat=True))

        permissions = list(
            Permission.objects.select_related('content_type')
            .exclude(content_type__app_label__in=EXCLUDED_PERMISSION_APP_LABELS)
            .order_by('content_type__app_label', 'content_type__model', 'codename')
        )

        app_map = {}
        for permission in permissions:
            app_label = permission.content_type.app_label
            model_name = permission.content_type.model
            app_entry = app_map.setdefault(app_label, {
                'app_label': app_label,
                'app_label_display': self._get_module_label(app_label),
                'models': {},
            })
            model_entry = app_entry['models'].setdefault(model_name, {
                'model_name': model_name,
                'model_label': permission.content_type.model_class()._meta.verbose_name.title() if permission.content_type.model_class() else model_name.replace('_', ' ').title(),
                'actions': {action: None for action in self.ACTION_ORDER},
                'custom_actions': [],
            })

            action_code = (permission.codename or '').split('_', 1)[0]
            expected_crud_codename = f'{action_code}_{model_name}'
            field_name = f'{self.FIELD_PREFIX}{permission.id}'
            self.fields[field_name] = forms.BooleanField(
                required=False,
                label=get_permission_label_fr(permission),
            )
            self.fields[field_name].initial = permission.id in current_permission_ids
            self._permission_field_names.append(field_name)

            permission_entry = {
                'field_name': field_name,
                'permission_id': permission.id,
                'codename': permission.codename,
                'label_fr': get_permission_label_fr(permission),
                'bound_field': self[field_name],
            }

            if action_code in self.ACTION_ORDER and permission.codename == expected_crud_codename:
                model_entry['actions'][action_code] = permission_entry
            else:
                model_entry['custom_actions'].append(permission_entry)

        self._permission_apps = []
        for app_label in sorted(app_map.keys()):
            models = list(app_map[app_label]['models'].values())
            models.sort(key=lambda item: item['model_label'])
            self._permission_apps.append({
                'app_label': app_map[app_label]['app_label'],
                'app_label_display': app_map[app_label]['app_label_display'],
                'models': models,
            })

    def _get_module_label(self, app_label):
        try:
            return django_apps.get_app_config(app_label).verbose_name.title()
        except LookupError:
            return app_label.replace('_', ' ').title()

    def get_module_fields(self):
        return []

    def get_permission_apps(self):
        return self._permission_apps

    def save(self):
        selected_permission_ids = [
            int(field_name.replace(self.FIELD_PREFIX, ''))
            for field_name in self._permission_field_names
            if self.cleaned_data.get(field_name)
        ]

        self.role_group.permissions.set(selected_permission_ids)
        return self.role_group

class UserForm(UserCreationForm):
    structure_text = forms.CharField(
        required=False,
        label='Structure',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tapez ou sélectionnez une structure',
            'list': 'structure-list'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'photo', 'password1', 'password2', 'is_staff', 'role')
        labels = {
            'username': 'Nom d\'utilisateur',
            'email': 'Email',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'photo': 'Photo',
            'is_staff': 'Personnel',
            'role': 'Rôle',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = User.ROLE_CHOICES
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        if self.instance and self.instance.pk and self.instance.structure:
            self.fields['structure_text'].initial = self.instance.structure.nom

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Les comptes nouvellement crees doivent etre valides par un administrateur.
        instance.is_active = False
        structure_text = self.cleaned_data.get('structure_text')
        if structure_text:
            structure, created = Structure.objects.get_or_create(nom=structure_text)
            instance.structure = structure
        else:
            instance.structure = None
        if commit:
            instance.save()
            self.save_m2m()
            sync_user_role_group(instance)
        return instance

class UserEditForm(UserChangeForm):
    structure_text = forms.CharField(
        required=False,
        label='Structure',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Tapez ou sélectionnez une structure',
            'list': 'structure-list'
        })
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'photo', 'is_active', 'is_staff', 'role', 'groups', 'user_permissions')
        labels = {
            'username': 'Nom d\'utilisateur',
            'email': 'Email',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'photo': 'Photo',
            'is_active': 'Actif',
            'is_staff': 'Personnel',
            'role': 'Rôle',
            'groups': 'Groupes',
            'user_permissions': 'Permissions directes',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'photo': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'groups': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '6'}),
            'user_permissions': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['role'].choices = User.ROLE_CHOICES
        self.fields['groups'].queryset = get_manual_groups_queryset()
        self.fields['user_permissions'].queryset = Permission.objects.select_related('content_type').exclude(
            content_type__app_label__in=EXCLUDED_PERMISSION_APP_LABELS
        ).order_by('content_type__app_label', 'name')
        if self.instance and self.instance.pk and self.instance.structure:
            self.fields['structure_text'].initial = self.instance.structure.nom

    def save(self, commit=True):
        instance = super().save(commit=False)
        structure_text = self.cleaned_data.get('structure_text')
        if structure_text:
            structure, created = Structure.objects.get_or_create(nom=structure_text)
            instance.structure = structure
        else:
            instance.structure = None
        if commit:
            instance.save()
            self.save_m2m()
            sync_user_role_group(instance)
        return instance
