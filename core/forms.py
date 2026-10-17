
from django import forms
from .models import College


class CollegeForm(forms.ModelForm):
    class Meta:
        model = College
        fields = ["name", "code", "email", "address", "is_active"]

        widgets = {
            "name": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Enter college name",
            }),
            "code": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "e.g. abc-college",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
                "placeholder": "college@example.com",
            }),
            "address": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Enter college address",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }
