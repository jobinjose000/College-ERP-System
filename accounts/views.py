
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
from .permissions import role_required

from accounts.models import StudentProfile, FacultyProfile
from academics.models import (
    FacultyAssignment,
    Timetable,
    Enrollment,
    Department,
    Course,
    ClassSection,
    ClassSession,
    Attendance,
)

from django.utils import timezone

from academics.models import ClassSession, Attendance
from django.db.models import Q

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
    college = request.user.college

    # Student statistics
    total_students = StudentProfile.objects.filter(
        user__college=college,
        user__role=User.Role.STUDENT,
        user__is_active=True,
    ).count()

    # Faculty statistics
    total_faculty = FacultyProfile.objects.filter(
        user__college=college,
        user__role=User.Role.FACULTY,
        user__is_active=True,
    ).count()

    # Academic statistics
    total_departments = Department.objects.filter(
        college=college,
    ).count()

    total_courses = Course.objects.filter(
        college=college,
        is_active=True,
    ).count()

    total_classes = ClassSection.objects.filter(
        college=college,
    ).count()

    # Current local date and time
    current_datetime = timezone.localtime()
    today = current_datetime.date()
    current_time = current_datetime.time().replace(tzinfo=None)

    # Today's class sessions
    today_sessions = ClassSession.objects.filter(
        faculty_assignment__college=college,
        class_section__college=college,
        date=today,
    ).select_related(
        "class_section",
        "class_section__department",
        "faculty_assignment",
        "faculty_assignment__faculty",
        "faculty_assignment__course",
    ).order_by("start_time")

    # Classes currently in progress
    ongoing_classes = today_sessions.filter(
        status=ClassSession.Status.SCHEDULED,
        start_time__lte=current_time,
        end_time__gt=current_time,
    )

    # Upcoming classes for today
    upcoming_classes = ClassSession.objects.filter(
    faculty_assignment__college=college,
    class_section__college=college,
    status=ClassSession.Status.SCHEDULED,
    ).filter(
        Q(date__gt=today)
        | Q(date=today, start_time__gt=current_time)
    ).select_related(
        "class_section",
        "faculty_assignment",
        "faculty_assignment__faculty",
        "faculty_assignment__course",
    ).order_by("date", "start_time")[:5]

    
    # Faculty availability based on today's timetable
    weekday_codes = {
        0: Timetable.Weekday.MONDAY,
        1: Timetable.Weekday.TUESDAY,
        2: Timetable.Weekday.WEDNESDAY,
        3: Timetable.Weekday.THURSDAY,
        4: Timetable.Weekday.FRIDAY,
        5: Timetable.Weekday.SATURDAY,
    }

    today_weekday = weekday_codes.get(today.weekday())

    faculty_profiles = FacultyProfile.objects.filter(
        user__college=college,
        user__role=User.Role.FACULTY,
        user__is_active=True,
    ).select_related("user").order_by("employee_id")

    faculty_availability = []

    for profile in faculty_profiles:

        # Get all timetable entries for this faculty member today
        schedule = Timetable.objects.filter(
            college=college,
            faculty=profile.user,
            weekday=today_weekday,
            is_active=True,
        ).select_related(
            "course",
            "period",
            "class_section",
            "class_section__department",
            "academic_year",
        ).order_by("period__number")

        # Find the class currently in progress
        current_class = schedule.filter(
            period__start_time__lte=current_time,
            period__end_time__gt=current_time,
        ).first()

        if current_class:
            availability_status = "IN_CLASS"

        elif schedule.exists():
            availability_status = "AVAILABLE"

        else:
            availability_status = "NOT_SCHEDULED"

        faculty_availability.append({
            "profile": profile,
            "status": availability_status,
            "current_class": current_class,
            "schedule": schedule,
        })


    # Today's attendance records
    today_attendance = Attendance.objects.filter(
        class_session__faculty_assignment__college=college,
        class_session__class_section__college=college,
        class_session__date=today,
    )

    present_count = today_attendance.filter(
        status=Attendance.Status.PRESENT,
    ).count()

    absent_count = today_attendance.filter(
        status=Attendance.Status.ABSENT,
    ).count()

    late_count = today_attendance.filter(
        status=Attendance.Status.LATE,
    ).count()

        # Attendance records grouped by status
    attendance_related_fields = [
        "student__user",
        "class_session__class_section",
        "class_session__class_section__department",
        "class_session__faculty_assignment__course",
    ]

    present_records = today_attendance.filter(
        status=Attendance.Status.PRESENT,
    ).select_related(*attendance_related_fields).order_by(
        "student__registration_number"
    )

    absent_records = today_attendance.filter(
        status=Attendance.Status.ABSENT,
    ).select_related(*attendance_related_fields).order_by(
        "student__registration_number"
    )

    late_records = today_attendance.filter(
        status=Attendance.Status.LATE,
    ).select_related(*attendance_related_fields).order_by(
        "student__registration_number"
    )

    return render(
        request,
        "accounts/college_admin_dashboard.html",
        {
            "total_students": total_students,
            "total_faculty": total_faculty,
            "total_departments": total_departments,
            "total_courses": total_courses,
            "total_classes": total_classes,

            "today": today,
            "today_sessions": today_sessions,
            "today_class_count": today_sessions.count(),
            "ongoing_classes": ongoing_classes,
            "upcoming_classes": upcoming_classes,

            "present_count": present_count,
            "absent_count": absent_count,
            "late_count": late_count,
            "present_records": present_records,
            "absent_records": absent_records,
            "late_records": late_records,

            "faculty_availability": faculty_availability,
        },
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

    timetable_entries = (
        Timetable.objects
        .filter(
            faculty=request.user,
            college=request.user.college,
            is_active=True,
        )
        .select_related(
            "academic_year",
            "class_section",
            "class_section__department",
            "course",
            "period",
        )
        .order_by("weekday", "period__number")
    )

    return render(
        request,
        "accounts/faculty_dashboard.html",
        {
            "assignments": assignments,
            "timetable_entries": timetable_entries,
        },
    )


@login_required
@role_required(User.Role.STUDENT)
def student_dashboard(request):
    enrollments = Enrollment.objects.filter(
        student__user=request.user,
        is_active=True,
    )

    timetable_entries = Timetable.objects.none()

    for enrollment in enrollments:
        timetable_entries = timetable_entries | Timetable.objects.filter(
            college=request.user.college,
            academic_year=enrollment.academic_year,
            class_section=enrollment.class_section,
            is_active=True,
        )

    timetable_entries = (
        timetable_entries
        .select_related(
            "period",
            "course",
            "faculty",
            "class_section",
            "class_section__department",
            "academic_year",
        )
        .order_by("weekday", "period__number")
        .distinct()
    )

    return render(
        request,
        "accounts/student_dashboard.html",
        {
            "timetable_entries": timetable_entries,
        },
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
