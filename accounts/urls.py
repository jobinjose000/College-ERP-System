
from django.urls import path

from . import views

urlpatterns = [
    path("", views.dashboard_redirect, name="dashboard"),
    path(
        "super-admin/",
        views.super_admin_dashboard,
        name="super_admin_dashboard",
    ),
    path(
        "college-admin/",
        views.college_admin_dashboard,
        name="college_admin_dashboard",
    ),
    path(
        "faculty/",
        views.faculty_dashboard,
        name="faculty_dashboard",
    ),
    path(
        "student/",
        views.student_dashboard,
        name="student_dashboard",
    ),
]
