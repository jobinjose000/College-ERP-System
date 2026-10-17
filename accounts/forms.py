
from django import forms
from django.contrib.auth import get_user_model

from core.models import College

User = get_user_model()


class UserManagementForm(forms.ModelForm):
    password = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "autocomplete": "new-password",
        }),
        help_text="Required for new users. Leave blank when editing.",
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "college",
            "is_active",
        ]

        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "email": forms.EmailInput(attrs={
                "class": "form-control",
            }),
            "first_name": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "last_name": forms.TextInput(attrs={
                "class": "form-control",
            }),
            "role": forms.Select(attrs={
                "class": "form-select",
            }),
            "college": forms.Select(attrs={
                "class": "form-select",
            }),
            "is_active": forms.CheckboxInput(attrs={
                "class": "form-check-input",
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["college"].queryset = College.objects.order_by("name")
        self.fields["college"].required = False

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        college = cleaned_data.get("college")
        password = cleaned_data.get("password")

        if role and role != User.Role.SUPER_ADMIN and not college:
            self.add_error(
                "college",
                "A college must be assigned to this role.",
            )

        if not self.instance.pk and not password:
            self.add_error(
                "password",
                "A password is required when creating a user.",
            )

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        password = self.cleaned_data.get("password")

        if password:
            user.set_password(password)

        if commit:
            user.save()
            self.save_m2m()

        return user
