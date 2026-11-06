
from django.contrib import admin

from .models import (
    AcademicYear,
    ClassSection,
    Course,
    Department,
    FacultyAssignment,
)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "college")
    search_fields = ("name", "code", "college__name")
    list_filter = ("college",)


@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "college",
        "start_date",
        "end_date",
        "is_active",
    )
    list_filter = ("college", "is_active")
    search_fields = ("name", "college__name")


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "name",
        "department",
        "college",
        "semester",
        "credits",
        "is_active",
    )
    list_filter = ("college", "department", "semester", "is_active")
    search_fields = ("code", "name")


@admin.register(ClassSection)
class ClassSectionAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "department",
        "academic_year",
        "semester",
        "college",
    )
    list_filter = ("college", "academic_year", "department", "semester")


@admin.register(FacultyAssignment)
class FacultyAssignmentAdmin(admin.ModelAdmin):
    list_display = (
        "faculty",
        "course",
        "class_section",
        "college",
    )
    list_filter = ("college", "course")
    search_fields = (
        "faculty__username",
        "course__code",
        "course__name",
    )
