from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import StudentProfile
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

from django.db import transaction
from .models import StudentProfile


class StudentManagementForm(forms.Form):
    # Student account details
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control"}),
    )
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "form-control",
                "autocomplete": "new-password",
            }
        ),
        min_length=8,
        help_text="Use at least 8 characters.",
    )

    # Academic details
    registration_number = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    department = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
    admission_year = forms.IntegerField(
        min_value=2000,
        max_value=2100,
        widget=forms.NumberInput(attrs={"class": "form-control"}),
    )
    date_of_birth = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={"class": "form-control", "type": "date"}
        ),
    )
    phone_number = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                "This username is already in use."
            )
        return username

    def clean_registration_number(self):
        registration_number = self.cleaned_data["registration_number"]
        if StudentProfile.objects.filter(
            registration_number=registration_number
        ).exists():
            raise forms.ValidationError(
                "This registration number is already in use."
            )
        return registration_number

    @transaction.atomic
    def save(self, college):
        user = User(
            username=self.cleaned_data["username"],
            email=self.cleaned_data["email"],
            first_name=self.cleaned_data["first_name"],
            last_name=self.cleaned_data["last_name"],
            role=User.Role.STUDENT,
            college=college,
            is_active=True,
        )
        user.set_password(self.cleaned_data["password"])
        user.save()

        StudentProfile.objects.create(
            user=user,
            registration_number=self.cleaned_data[
                "registration_number"
            ],
            department=self.cleaned_data["department"],
            admission_year=self.cleaned_data["admission_year"],
            date_of_birth=self.cleaned_data["date_of_birth"],
            phone_number=self.cleaned_data["phone_number"],
        )

        return user
