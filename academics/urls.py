from django.urls import path

from . import views


urlpatterns = [
    path(
        "enrollments/",
        views.enrollment_list,
        name="enrollment_list",
    ),
    path(
        "enrollments/add/",
        views.enrollment_create,
        name="enrollment_create",
    ),
    path(
        "faculty/assignments/<int:assignment_id>/students/",
        views.assigned_class_students,
        name="assigned_class_students",
    ),
]