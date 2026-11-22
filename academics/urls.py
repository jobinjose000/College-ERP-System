
from django.urls import path

from . import views


urlpatterns = [
    # Student Enrollment
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

    # Faculty - Assigned Students
    path(
        "faculty/assignments/<int:assignment_id>/students/",
        views.assigned_class_students,
        name="assigned_class_students",
    ),

    # Faculty - Period-wise Attendance
    path(
        "faculty/sessions/<int:session_id>/attendance/",
        views.mark_attendance,
        name="mark_attendance",
    ),
    path(
        "faculty/assignments/<int:assignment_id>/sessions/",
        views.faculty_sessions,
        name="faculty_sessions",
    ),

    # Timetable Management
    path(
        "timetable/",
        views.timetable_list,
        name="timetable_list",
    ),
    path(
        "timetable/add/",
        views.timetable_create,
        name="timetable_create",
    ),
]
