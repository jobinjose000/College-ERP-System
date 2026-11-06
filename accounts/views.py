
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render

from core.models import College
from .forms import (
    UserManagementForm,
    StudentManagementForm,
    FacultyManagementForm,
)
from .models import StudentProfile, FacultyProfile
from .permissions import role_required

from academics.models import FacultyAssignment


User = get_user_model()


# --------------------------------------------------
# Dashboard Views
# --------------------------------------------------

@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard for their ERP role."""

    role_dashboards = {
        User.Role.SUPER_ADMIN: "super_admin_dashboard",
        User.Role.COLLEGE_ADMIN: "college_admin_dashboard",
        User.Role.FACULTY: "faculty_dashboard",
        User.Role.STUDENT: "student_dashboard",
    }

    dashboard_url = role_dashboards.get(request.user.role)

    if dashboard_url:
        return redirect(dashboard_url)

    return render(
        request,
        "accounts/role_error.html",
        status=403,
    )


@login_required
@role_required(User.Role.SUPER_ADMIN)
def super_admin_dashboard(request):
    return render(
        request,
        "accounts/super_admin_dashboard.html",
    )


@login_required
@role_required(User.Role.COLLEGE_ADMIN)
def college_admin_dashboard(request):
    return render(
        request,
        "accounts/college_admin_dashboard.html",
    )


@login_required
@role_required(User.Role.FACULTY)
def faculty_dashboard(request):
    assignments = (
        FacultyAssignment.objects
        .filter(
            faculty=request.user,
            college=request.user.college,
        )
        .select_related(
            "course",
            "course__department",
            "class_section",
            "class_section__academic_year",
        )
        .order_by("course__code")
    )

    return render(
        request,
        "accounts/faculty_dashboard.html",
        {
            "assignments": assignments,
        },
    )


@login_required
@role_required(User.Role.STUDENT)
def student_dashboard(request):
    return render(
        request,
        "accounts/student_dashboard.html",
    )


# --------------------------------------------------
# Shared Helper
# --------------------------------------------------

def get_active_college_from_post(request, form, error_message):
    """
    Validate the submitted college ID for a Super Admin.

    Return an active college or None if the submitted ID is
    missing or invalid. Invalid selections become form errors.
    """
    college_id = request.POST.get("college_id")

    if not college_id:
        form.add_error(None, error_message)
        return None

    try:
        college = College.objects.filter(
            is_active=True,
        ).get(pk=college_id)
    except (College.DoesNotExist, ValueError, TypeError):
        form.add_error(
            None,
            "Select a valid active college.",
        )
        return None

    return college


# --------------------------------------------------
# User Management
# --------------------------------------------------

@role_required(User.Role.SUPER_ADMIN, User.Role.COLLEGE_ADMIN)
def user_list(request):
    if request.user.role == User.Role.SUPER_ADMIN:
        users = User.objects.select_related(
            "college",
        ).order_by("username")
    else:
        users = User.objects.filter(
            college_id=request.user.college_id,
        ).select_related(
            "college",
        ).order_by("username")

    return render(
        request,
        "accounts/user_list.html",
        {"users": users},
    )


@role_required(User.Role.SUPER_ADMIN, User.Role.COLLEGE_ADMIN)
def user_create(request):
    if request.method == "POST":
        form = UserManagementForm(request.POST)

        if form.is_valid():
            new_user = form.save(commit=False)

            if request.user.role == User.Role.COLLEGE_ADMIN:
                if request.user.college_id is None:
                    raise PermissionDenied(
                        "Your account is not assigned to a college."
                    )

                if new_user.role == User.Role.SUPER_ADMIN:
                    form.add_error(
                        "role",
                        "College Admins cannot create Super Admin accounts.",
                    )
                else:
                    # Always assign the logged-in admin's college.
                    new_user.college = request.user.college
                    new_user.save()
                    form.save_m2m()

                    messages.success(
                        request,
                        "User account created successfully.",
                    )
                    return redirect("user_list")

            else:
                new_user.save()
                form.save_m2m()

                messages.success(
                    request,
                    "User account created successfully.",
                )
                return redirect("user_list")
    else:
        form = UserManagementForm()

    if request.user.role == User.Role.COLLEGE_ADMIN:
        form.fields["college"].disabled = True

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "page_title": "Create User",
        },
    )


@role_required(User.Role.SUPER_ADMIN, User.Role.COLLEGE_ADMIN)
def user_edit(request, user_id):
    managed_user = get_object_or_404(
        User,
        pk=user_id,
    )

    if request.user.role == User.Role.COLLEGE_ADMIN:
        if (
            request.user.college_id is None
            or managed_user.college_id != request.user.college_id
        ):
            raise PermissionDenied(
                "You cannot edit users from another college."
            )

        if managed_user.role == User.Role.SUPER_ADMIN:
            raise PermissionDenied(
                "You cannot edit a Super Admin account."
            )

    if request.method == "POST":
        form = UserManagementForm(
            request.POST,
            instance=managed_user,
        )

        if form.is_valid():
            updated_user = form.save(commit=False)

            if request.user.role == User.Role.COLLEGE_ADMIN:
                if updated_user.role == User.Role.SUPER_ADMIN:
                    form.add_error(
                        "role",
                        "College Admins cannot assign the Super Admin role.",
                    )
                else:
                    # Prevent reassignment to another college.
                    updated_user.college = request.user.college
                    updated_user.save()
                    form.save_m2m()

                    messages.success(
                        request,
                        "User account updated successfully.",
                    )
                    return redirect("user_list")

            else:
                updated_user.save()
                form.save_m2m()

                messages.success(
                    request,
                    "User account updated successfully.",
                )
                return redirect("user_list")
    else:
        form = UserManagementForm(
            instance=managed_user,
        )

    if request.user.role == User.Role.COLLEGE_ADMIN:
        form.fields["college"].disabled = True
        form.fields["role"].choices = [
            choice
            for choice in form.fields["role"].choices
            if choice[0] != User.Role.SUPER_ADMIN
        ]

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "page_title": "Edit User",
            "managed_user": managed_user,
        },
    )


# --------------------------------------------------
# Student Management
# --------------------------------------------------

@role_required(User.Role.SUPER_ADMIN, User.Role.COLLEGE_ADMIN)
def student_list(request):
    students = StudentProfile.objects.select_related(
        "user",
        "user__college",
    ).order_by("registration_number")

    if request.user.role == User.Role.COLLEGE_ADMIN:
        students = students.filter(
            user__college_id=request.user.college_id,
        )

    return render(
        request,
        "accounts/student_list.html",
        {"students": students},
    )


@role_required(User.Role.SUPER_ADMIN, User.Role.COLLEGE_ADMIN)
def student_create(request):
    if (
        request.user.role == User.Role.COLLEGE_ADMIN
        and request.user.college_id is None
    ):
        raise PermissionDenied(
            "Your account is not assigned to a college."
        )

    if request.method == "POST":
        form = StudentManagementForm(request.POST)

        if form.is_valid():
            if request.user.role == User.Role.SUPER_ADMIN:
                college = get_active_college_from_post(
                    request,
                    form,
                    "Please select a college for this student.",
                )

                if college is not None:
                    form.save(college=college)

                    messages.success(
                        request,
                        "Student account created successfully.",
                    )
                    return redirect("student_list")

            else:
                # Never trust a submitted college ID from a College Admin.
                form.save(college=request.user.college)

                messages.success(
                    request,
                    "Student account created successfully.",
                )
                return redirect("student_list")
    else:
        form = StudentManagementForm()

    colleges = College.objects.filter(
        is_active=True,
    ).order_by("name")

    return render(
        request,
        "accounts/student_form.html",
        {
            "form": form,
            "colleges": colleges,
            "page_title": "Add Student",
        },
    )


# --------------------------------------------------
# Faculty Management
# --------------------------------------------------

@role_required(User.Role.SUPER_ADMIN, User.Role.COLLEGE_ADMIN)
def faculty_list(request):
    faculty_members = FacultyProfile.objects.select_related(
        "user",
        "user__college",
    ).order_by("employee_id")

    if request.user.role == User.Role.COLLEGE_ADMIN:
        faculty_members = faculty_members.filter(
            user__college_id=request.user.college_id,
        )

    return render(
        request,
        "accounts/faculty_list.html",
        {"faculty_members": faculty_members},
    )


@role_required(User.Role.SUPER_ADMIN, User.Role.COLLEGE_ADMIN)
def faculty_create(request):
    if (
        request.user.role == User.Role.COLLEGE_ADMIN
        and request.user.college_id is None
    ):
        raise PermissionDenied(
            "Your account is not assigned to a college."
        )

    if request.method == "POST":
        form = FacultyManagementForm(request.POST)

        if form.is_valid():
            if request.user.role == User.Role.SUPER_ADMIN:
                college = get_active_college_from_post(
                    request,
                    form,
                    "Please select a college for this faculty member.",
                )

                if college is not None:
                    form.save(college=college)

                    messages.success(
                        request,
                        "Faculty account created successfully.",
                    )
                    return redirect("faculty_list")

            else:
                # College Admins can only create faculty in their college.
                form.save(college=request.user.college)

                messages.success(
                    request,
                    "Faculty account created successfully.",
                )
                return redirect("faculty_list")
    else:
        form = FacultyManagementForm()

    colleges = College.objects.filter(
        is_active=True,
    ).order_by("name")

    return render(
        request,
        "accounts/faculty_form.html",
        {
            "form": form,
            "colleges": colleges,
            "page_title": "Add Faculty",
        },
    )
