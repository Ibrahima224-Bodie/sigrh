from django import forms
from .models import Direction

class DirectionForm(forms.ModelForm):
    class Meta:
        model = Direction
        fields = '__all__'
        labels = {
            'nom': 'Nom',
            'sigle': 'Sigle',
            'description': 'Description',
        }
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la direction'}),
            'sigle': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Sigle'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
        }
