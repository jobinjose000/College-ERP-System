
from django.contrib import admin

from .models import (
    AcademicYear,
    Attendance,
    ClassSection,
    ClassSession,
    Course,
    Department,
    Enrollment,
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


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "academic_year",
        "class_section",
        "enrolled_at",
        "is_active",
    )
    list_filter = (
        "academic_year",
        "class_section",
        "is_active",
    )
    search_fields = (
        "student__registration_number",
        "student__user__username",
    )


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "student",
        "class_session",
        "status",
        "created_at",
    )

    list_filter = (
        "status",
        "class_session__date",
        "class_session__period_number",
        "class_session__faculty_assignment__college",
        "class_session__faculty_assignment__course",
    )

    search_fields = (
        "student__registration_number",
        "student__user__username",
        "class_session__faculty_assignment__course__code",
        "class_session__faculty_assignment__faculty__username",
    )

    date_hierarchy = "class_session__date"


@admin.register(ClassSession)
class ClassSessionAdmin(admin.ModelAdmin):

    list_display = (
        "class_section",
        "faculty_assignment",
        "date",
        "period_number",
        "start_time",
        "end_time",
        "status",
    )

    list_filter = (
        "date",
        "status",
        "period_number",
        "class_section__college",
    )

    search_fields = (
        "class_section__name",
        "faculty_assignment__course__code",
        "faculty_assignment__faculty__username",
        "topic",
    )

    date_hierarchy = "date"
    