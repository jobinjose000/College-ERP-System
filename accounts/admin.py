
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User , FacultyProfile, StudentProfile


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

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = (
        "registration_number",
        "user",
        "department",
        "admission_year",
        "phone_number",
    )
    search_fields = (
        "registration_number",
        "user__username",
        "user__email",
        "department",
    )
    list_filter = ("department", "admission_year")


@admin.register(FacultyProfile)
class FacultyProfileAdmin(admin.ModelAdmin):
    list_display = (
        "employee_id",
        "user",
        "department",
        "designation",
        "phone_number",
    )
    search_fields = (
        "employee_id",
        "user__username",
        "user__email",
        "department",
    )
    list_filter = ("department", "designation")
