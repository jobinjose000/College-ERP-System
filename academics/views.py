
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from accounts.models import User
from accounts.permissions import role_required

from .forms import EnrollmentForm
from .models import Enrollment, FacultyAssignment, Attendance, ClassSession



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
        .select_related("student", "student__user")
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


@login_required
@role_required(User.Role.FACULTY)
def mark_attendance(request, session_id):

    session = get_object_or_404(
        ClassSession.objects.select_related(
            "class_section",
            "class_section__department",
            "class_section__academic_year",
            "faculty_assignment",
            "faculty_assignment__course",
            "faculty_assignment__faculty",
        ),
        id=session_id,
        faculty_assignment__faculty=request.user,
        faculty_assignment__college=request.user.college,
    )

    enrollments = (
        Enrollment.objects.filter(
            class_section=session.class_section,
            academic_year=session.class_section.academic_year,
            is_active=True,
            student__user__college=request.user.college,
        )
        .select_related("student", "student__user")
        .order_by("student__registration_number")
    )

    if request.method == "POST":

        try:
            with transaction.atomic():

                for enrollment in enrollments:

                    student = enrollment.student

                    status = request.POST.get(f"status_{student.id}", "")

                    # Skip students whose attendance has not been marked.
                    if status == "":
                        # Remove an existing record if the faculty selects Not Marked.
                        Attendance.objects.filter(
                            student=student,
                            class_session=session,
                        ).delete()
                        continue

                    valid_statuses = dict(Attendance.Status.choices)

                    if status not in valid_statuses:
                        raise ValidationError(
                            f"Invalid attendance status for {student.registration_number}."
                        )

                    attendance, created = Attendance.objects.get_or_create(
                        student=student,
                        class_session=session,
                        defaults={"status": status},
                    )

                    if not created:
                        attendance.status = status

                    attendance.full_clean()
                    attendance.save()
            return redirect(
                "faculty_sessions",
                assignment_id=session.faculty_assignment_id,
            )

        except ValidationError as error:
            messages.error(
                request,
                "Could not save attendance: "
                + " ".join(error.messages),
            )

    attendance_records = Attendance.objects.filter(
        class_session=session,
    ).select_related("student", "student__user")

    attendance_by_student = {
        record.student_id: record.status
        for record in attendance_records
    }

    for enrollment in enrollments:
        enrollment.attendance_status = attendance_by_student.get(
            enrollment.student_id, "",
        )

    return render(
        request,
        "academics/attendance_marking.html",
        {
            "session": session,
            "enrollments": enrollments,
            "attendance_by_student": attendance_by_student,
        },
    )


@login_required
@role_required(User.Role.FACULTY)
def faculty_sessions(request, assignment_id):
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

    sessions = ClassSession.objects.filter(
        faculty_assignment=assignment,
    ).order_by("date", "period_number")

    for session in sessions:
        enrolled_count = Enrollment.objects.filter(
            class_section=session.class_section,
            academic_year=session.class_section.academic_year,
            is_active=True,
            student__user__college=request.user.college,
        ).count()

        attendance_count = Attendance.objects.filter(
            class_session=session,
            student__user__college=request.user.college,
        ).count()

        session.attendance_recorded = attendance_count > 0

        session.attendance_complete = (
            enrolled_count > 0
            and attendance_count == enrolled_count
        )

    return render(
        request,
        "academics/faculty_sessions.html",
        {
            "assignment": assignment,
            "sessions": sessions,
        },
    )

