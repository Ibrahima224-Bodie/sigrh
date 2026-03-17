from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User
from apps.organigramme.models import Structure

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
        fields = ('username', 'email', 'first_name', 'last_name', 'password1', 'password2', 'is_active', 'is_staff', 'role')
        labels = {
            'username': 'Nom d\'utilisateur',
            'email': 'Email',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'is_active': 'Actif',
            'is_staff': 'Personnel',
            'role': 'Rôle',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom d\'utilisateur'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tapez ou sélectionnez un rôle', 'list': 'role-list'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        fields = ('username', 'email', 'first_name', 'last_name', 'is_active', 'is_staff', 'role')
        labels = {
            'username': 'Nom d\'utilisateur',
            'email': 'Email',
            'first_name': 'Prénom',
            'last_name': 'Nom',
            'is_active': 'Actif',
            'is_staff': 'Personnel',
            'role': 'Rôle',
        }
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom'}),
            'role': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tapez ou sélectionnez un rôle', 'list': 'role-list'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        return instance
