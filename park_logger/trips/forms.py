from django import forms
from .models import Trip

class TripForm(forms.ModelForm):
    class Meta:
        model = Trip
        fields = ['park', 'visit_date', 'rating', 'comments', 'image']
        widgets = {
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
        }
