
from django.contrib.auth import views as auth_views
from django.urls import path
from . import views

urlpatterns = [
    # Authentication
    path("login/",auth_views.LoginView.as_view(template_name="accounts/login.html"),name="login",),
    path("logout/",auth_views.LogoutView.as_view(),name="logout",),

    # Role-based dashboards
    path("", views.dashboard_redirect, name="dashboard"),
    path("super-admin/",views.super_admin_dashboard,name="super_admin_dashboard",),
    path("college-admin/",views.college_admin_dashboard,name="college_admin_dashboard",),
    path("faculty/", views.faculty_dashboard, name="faculty_dashboard"),
    path("student/", views.student_dashboard, name="student_dashboard"),
    
    path("users/", views.user_list, name="user_list"),
    path("users/add/", views.user_create, name="user_create"),
    path("users/<int:user_id>/edit/",views.user_edit,name="user_edit",),

    
    path("students/", views.student_list, name="student_list"),
    path("students/add/", views.student_create, name="student_create"),


]
