from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.permissions import role_required

from .forms import EnrollmentForm
from .models import Enrollment, FacultyAssignment


@login_required
@role_required(User.Role.SUPER_ADMIN, User.Role.COLLEGE_ADMIN)
def enrollment_list(request):

    if request.user.role == User.Role.SUPER_ADMIN:
        enrollments = Enrollment.objects.all()

    else:
        enrollments = Enrollment.objects.filter(
            student__user__college=request.user.college,
            class_section__college=request.user.college,
        )

    enrollments = enrollments.select_related(
        "student",
        "student__user",
        "academic_year",
        "class_section",
        "class_section__department",
    ).order_by("-enrolled_at")

    return render(
        request,
        "academics/enrollment_list.html",
        {"enrollments": enrollments},
    )


@login_required
@role_required(User.Role.SUPER_ADMIN, User.Role.COLLEGE_ADMIN)
def enrollment_create(request):

    if request.method == "POST":
        form = EnrollmentForm(
            request.POST,
            user=request.user,
        )

        if form.is_valid():
            enrollment = form.save(commit=False)

            enrollment.full_clean()
            enrollment.save()

            messages.success(
                request,
                "Student enrolled successfully.",
            )

            return redirect("enrollment_list")

    else:
        form = EnrollmentForm(user=request.user)

    return render(
        request,
        "academics/enrollment_form.html",
        {"form": form},
    )


@login_required
@role_required(User.Role.FACULTY)
def assigned_class_students(request, assignment_id):

    assignment = get_object_or_404(
        FacultyAssignment.objects.select_related(
            "course",
            "class_section",
            "class_section__department",
            "class_section__academic_year",
        ),
        id=assignment_id,
        faculty=request.user,
        college=request.user.college,
    )

    enrollments = (
        Enrollment.objects.filter(
            class_section=assignment.class_section,
            academic_year=assignment.class_section.academic_year,
            is_active=True,
            student__user__college=request.user.college,
        )
        .select_related(
            "student",
            "student__user",
        )
        .order_by("student__registration_number")
    )

    return render(
        request,
        "academics/assigned_class_students.html",
        {
            "assignment": assignment,
            "enrollments": enrollments,
        },
    )