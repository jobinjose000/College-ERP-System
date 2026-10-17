
from django.contrib.auth.decorators import login_required
from .permissions import role_required
from django.shortcuts import redirect, render
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404

from .forms import UserManagementForm

@login_required
def dashboard_redirect(request):
    """Send each user to the dashboard for their ERP role."""

    role_dashboards = {
        "SUPER_ADMIN": "super_admin_dashboard",
        "COLLEGE_ADMIN": "college_admin_dashboard",
        "FACULTY": "faculty_dashboard",
        "STUDENT": "student_dashboard",
    }

    dashboard_url = role_dashboards.get(request.user.role)

    if dashboard_url:
        return redirect(dashboard_url)

    return render(request, "accounts/role_error.html", status=403)


@login_required
def super_admin_dashboard(request):
    if request.user.role != "SUPER_ADMIN":
        return render(request, "accounts/role_error.html", status=403)

    return render(request, "accounts/super_admin_dashboard.html")


@login_required
def college_admin_dashboard(request):
    if request.user.role != "COLLEGE_ADMIN":
        return render(request, "accounts/role_error.html", status=403)

    return render(request, "accounts/college_admin_dashboard.html")


@login_required
def faculty_dashboard(request):
    if request.user.role != "FACULTY":
        return render(request, "accounts/role_error.html", status=403)

    return render(request, "accounts/faculty_dashboard.html")


@login_required
def student_dashboard(request):
    if request.user.role != "STUDENT":
        return render(request, "accounts/role_error.html", status=403)

    return render(request, "accounts/student_dashboard.html")



User = get_user_model()


@login_required
@role_required(User.Role.SUPER_ADMIN)
def user_list(request):
    users = User.objects.select_related("college").order_by("username")

    return render(
        request,
        "accounts/user_list.html",
        {"users": users},
    )


@login_required
@role_required(User.Role.SUPER_ADMIN)
def user_create(request):
    if request.method == "POST":
        form = UserManagementForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(request, "User account created successfully.")
            return redirect("user_list")
    else:
        form = UserManagementForm()

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "page_title": "Create User",
        },
    )


@login_required
@role_required(User.Role.SUPER_ADMIN)
def user_edit(request, user_id):
    managed_user = get_object_or_404(User, pk=user_id)

    if request.method == "POST":
        form = UserManagementForm(request.POST, instance=managed_user)

        if form.is_valid():
            form.save()
            messages.success(request, "User account updated successfully.")
            return redirect("user_list")
    else:
        form = UserManagementForm(instance=managed_user)

    return render(
        request,
        "accounts/user_form.html",
        {
            "form": form,
            "page_title": "Edit User",
            "managed_user": managed_user,
        },
    )
