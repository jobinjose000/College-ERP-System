
from django.contrib import admin
from .models import College


@admin.register(College)
class CollegeAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "email", "is_active", "created_at")
    search_fields = ("name", "code", "email")
    list_filter = ("is_active",)
    readonly_fields = ("created_at",)
    prepopulated_fields = {"code": ("name",)}
