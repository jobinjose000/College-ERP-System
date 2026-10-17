
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "college",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "college", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        (
            "College ERP Information",
            {"fields": ("role", "college")},
        ),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (
            "College ERP Information",
            {"fields": ("role", "college")},
        ),
    )
