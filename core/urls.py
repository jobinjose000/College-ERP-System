
from django.urls import path
from . import views

urlpatterns = [
    path("colleges/", views.college_list, name="college_list"),
    path("colleges/add/", views.college_create, name="college_create"),
    path("colleges/<int:college_id>/edit/",views.college_edit,name="college_edit",),
    path("colleges/<int:college_id>/toggle-status/",views.college_toggle_status,name="college_toggle_status",),
]
