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
]