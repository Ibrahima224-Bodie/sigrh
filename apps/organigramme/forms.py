from django import forms
from .models import Structure

class StructureForm(forms.ModelForm):
    class Meta:
        model = Structure
        fields = '__all__'
        labels = {
            'nom': 'Nom',
            'sigle': 'Sigle',
            'type_structure': 'Type de Structure',
            'structure_parent': 'Structure Parente',
            'description': 'Description',
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la structure'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigle'}),
            'type_structure': forms.Select(attrs={'class': 'form-control'}),
            'structure_parent': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
        }
