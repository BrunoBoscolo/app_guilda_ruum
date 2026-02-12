from django import forms
from .models import Monster

class MonsterForm(forms.ModelForm):
    class Meta:
        model = Monster
        exclude = ['slug', 'created_at', 'updated_at']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'weaknesses': forms.Textarea(attrs={'rows': 3}),
            'immunities': forms.Textarea(attrs={'rows': 3}),
            'special_abilities': forms.Textarea(attrs={'rows': 4}),
        }
