
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.permissions import role_required
from .forms import CollegeForm
from .models import College


@login_required
@role_required(User.Role.SUPER_ADMIN)
def college_list(request):
    colleges = College.objects.all().order_by("name")

    return render(
        request,
        "core/college_list.html",
        {"colleges": colleges},
    )


@login_required
@role_required(User.Role.SUPER_ADMIN)
def college_create(request):
    if request.method == "POST":
        form = CollegeForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("college_list")
    else:
        form = CollegeForm()

    return render(
        request,
        "core/college_form.html",
        {
            "form": form,
            "page_title": "Add College",
        },
    )


@login_required
@role_required(User.Role.SUPER_ADMIN)
def college_edit(request, college_id):
    college = get_object_or_404(College, pk=college_id)

    if request.method == "POST":
        form = CollegeForm(request.POST, instance=college)

        if form.is_valid():
            form.save()
            return redirect("college_list")
    else:
        form = CollegeForm(instance=college)

    return render(
        request,
        "core/college_form.html",
        {
            "form": form,
            "page_title": "Edit College",
            "college": college,
        },
    )
