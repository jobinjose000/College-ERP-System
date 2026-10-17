
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render


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
