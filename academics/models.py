
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from accounts.models import StudentProfile

class Department(models.Model):
    college = models.ForeignKey(
        "core.College",
        on_delete=models.PROTECT,
        related_name="departments",
    )
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["college", "name"],
                name="unique_department_name_per_college",
            ),
            models.UniqueConstraint(
                fields=["college", "code"],
                name="unique_department_code_per_college",
            ),
        ]
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.college.name})"


class AcademicYear(models.Model):
    college = models.ForeignKey(
        "core.College",
        on_delete=models.PROTECT,
        related_name="academic_years",
    )
    name = models.CharField(max_length=20)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["college", "name"],
                name="unique_academic_year_per_college",
            ),
        ]
        ordering = ["-start_date"]

    def clean(self):
        if self.end_date <= self.start_date:
            raise ValidationError(
                "End date must be after start date."
            )

    def __str__(self):
        return f"{self.name} - {self.college.name}"


class Course(models.Model):
    college = models.ForeignKey(
        "core.College",
        on_delete=models.PROTECT,
        related_name="courses",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="courses",
    )
    code = models.CharField(max_length=20)
    name = models.CharField(max_length=150)
    credits = models.PositiveSmallIntegerField(default=3)
    semester = models.PositiveSmallIntegerField()
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["college", "code"],
                name="unique_course_code_per_college",
            ),
        ]
        ordering = ["code"]

    def clean(self):
        if self.department_id and self.college_id:
            if self.department.college_id != self.college_id:
                raise ValidationError(
                    "Department must belong to the same college."
                )

    def __str__(self):
        return f"{self.code} - {self.name}"


class ClassSection(models.Model):
    college = models.ForeignKey(
        "core.College",
        on_delete=models.PROTECT,
        related_name="class_sections",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="class_sections",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name="class_sections",
    )
    name = models.CharField(max_length=30)
    semester = models.PositiveSmallIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "academic_year",
                    "department",
                    "name",
                    "semester",
                ],
                name="unique_class_section_per_year",
            ),
        ]
        ordering = ["department", "semester", "name"]

    def clean(self):
        if self.college_id:
            if self.department_id:
                if self.department.college_id != self.college_id:
                    raise ValidationError(
                        "Department must belong to the same college."
                    )

            if self.academic_year_id:
                if self.academic_year.college_id != self.college_id:
                    raise ValidationError(
                        "Academic year must belong to the same college."
                    )

    def __str__(self):
        return (
            f"{self.department.name} - Semester "
            f"{self.semester} - {self.name}"
        )


class FacultyAssignment(models.Model):
    college = models.ForeignKey(
        "core.College",
        on_delete=models.PROTECT,
        related_name="faculty_assignments",
    )
    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        limit_choices_to={"role": "FACULTY"},
        related_name="academic_assignments",
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.PROTECT,
        related_name="faculty_assignments",
    )
    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.PROTECT,
        related_name="faculty_assignments",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["faculty", "course", "class_section"],
                name="unique_faculty_course_section",
            ),
        ]

    def clean(self):
        if not self.college_id:
            return

        if self.faculty_id:
            if self.faculty.college_id != self.college_id:
                raise ValidationError(
                    "Faculty must belong to the same college."
                )

            if self.faculty.role != "FACULTY":
                raise ValidationError(
                    "Only faculty users can receive assignments."
                )

        if self.course_id:
            if self.course.college_id != self.college_id:
                raise ValidationError(
                    "Course must belong to the same college."
                )

        if self.class_section_id:
            if self.class_section.college_id != self.college_id:
                raise ValidationError(
                    "Class section must belong to the same college."
                )

        if self.course_id and self.class_section_id:
            if (
                self.course.department_id
                != self.class_section.department_id
            ):
                raise ValidationError(
                    "Course and class section must belong to "
                    "the same department."
                )

    def __str__(self):
        return (
            f"{self.faculty.username} - "
            f"{self.course.code} - "
            f"{self.class_section.name}"
        )

class Enrollment(models.Model):
    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    enrolled_at = models.DateField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "academic_year"],
                name="unique_student_enrollment_per_year",
            ),
        ]
        ordering = ["student__registration_number"]

    def clean(self):
        if not self.student_id or not self.class_section_id:
            return

        if self.student.user.role != "STUDENT":
            raise ValidationError(
                "Only student accounts can be enrolled."
            )

        if (
            self.student.user.college_id
            != self.class_section.college_id
        ):
            raise ValidationError(
                "Student and class must belong to the same college."
            )

        if (
            self.academic_year_id
            != self.class_section.academic_year_id
        ):
            raise ValidationError(
                "Academic year must match the class section."
            )

        if (
            self.student.department
            != self.class_section.department.name
        ):
            raise ValidationError(
                "Student and class must belong to the same department."
            )

    def __str__(self):
        return (
            f"{self.student.registration_number} - "
            f"{self.class_section}"
        )



class Attendance(models.Model):

    class Status(models.TextChoices):
        PRESENT = "PRESENT", "Present"
        ABSENT = "ABSENT", "Absent"
        LATE = "LATE", "Late"

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.PROTECT,
        related_name="attendance_records",
    )

    class_session = models.ForeignKey(
        "ClassSession",
        on_delete=models.PROTECT,
        related_name="attendance_records",
        null=True,
        blank=True,
    )

    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.PRESENT,
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "class_session"],
                name="unique_student_attendance_per_session",
            ),
        ]
        ordering = ["student__registration_number"]

    def clean(self):
        if not self.student_id or not self.class_session_id:
            return

        session = self.class_session
        assignment = session.faculty_assignment

        if self.student.user.role != "STUDENT":
            raise ValidationError(
                "Attendance can only be recorded for students."
            )

        if self.student.user.college_id != assignment.college_id:
            raise ValidationError(
                "Student and class session must belong to the same college."
            )

        if not Enrollment.objects.filter(
            student=self.student,
            academic_year=session.class_section.academic_year,
            class_section=session.class_section,
            is_active=True,
        ).exists():
            raise ValidationError(
                "Student must be actively enrolled in this class."
            )

        if self.status == self.Status.LATE and session.period_number != 1:
            raise ValidationError(
                "Late attendance is only allowed in Period 1."
            )

    def __str__(self):
        return (
            f"{self.student.registration_number} - "
            f"{self.class_session} - {self.status}"
        )




class ClassSession(models.Model):

    class Status(models.TextChoices):
        SCHEDULED = "SCHEDULED", "Scheduled"
        COMPLETED = "COMPLETED", "Completed"
        CANCELLED = "CANCELLED", "Cancelled"

    class_section = models.ForeignKey(
        ClassSection,
        on_delete=models.PROTECT,
        related_name="class_sessions",
    )

    faculty_assignment = models.ForeignKey(
        FacultyAssignment,
        on_delete=models.PROTECT,
        related_name="class_sessions",
    )

    date = models.DateField()

    period_number = models.PositiveSmallIntegerField()

    start_time = models.TimeField()

    end_time = models.TimeField()

    classroom = models.CharField(
        max_length=50,
        blank=True,
    )

    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.SCHEDULED,
    )

    topic = models.CharField(
        max_length=200,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    "class_section",
                    "date",
                    "period_number",
                ],
                name="unique_class_section_period_per_day",
            ),
        ]
        ordering = ["date", "period_number"]

    def clean(self):

        if not self.class_section_id or not self.faculty_assignment_id:
            return

        assignment = self.faculty_assignment

        if assignment.class_section_id != self.class_section_id:
            raise ValidationError(
                "Faculty assignment must belong to this class section."
            )

        if assignment.college_id != self.class_section.college_id:
            raise ValidationError(
                "Faculty assignment and class must belong to the same college."
            )

        if self.end_time <= self.start_time:
            raise ValidationError(
                "End time must be after start time."
            )

    def __str__(self):
        return (
            f"{self.class_section} - "
            f"Period {self.period_number} - "
            f"{self.date}"
        )


class Period(models.Model):
    college = models.ForeignKey(
        "core.College",
        on_delete=models.CASCADE,
        related_name="periods",
    )
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=50, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["number"]
        constraints = [
            models.UniqueConstraint(
                fields=["college", "number"],
                name="unique_period_number_per_college",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.end_time <= self.start_time:
            raise ValidationError(
                "Period end time must be after start time."
            )

    def __str__(self):
        return f"Period {self.number} - {self.college.name}"


class Timetable(models.Model):

    class Weekday(models.TextChoices):
        MONDAY = "MON", "Monday"
        TUESDAY = "TUE", "Tuesday"
        WEDNESDAY = "WED", "Wednesday"
        THURSDAY = "THU", "Thursday"
        FRIDAY = "FRI", "Friday"
        SATURDAY = "SAT", "Saturday"

    college = models.ForeignKey(
        "core.College",
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )
    academic_year = models.ForeignKey(
        "academics.AcademicYear",
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )
    class_section = models.ForeignKey(
        "academics.ClassSection",
        on_delete=models.CASCADE,
        related_name="timetable_entries",
    )
    period = models.ForeignKey(
        "academics.Period",
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )
    course = models.ForeignKey(
        "academics.Course",
        on_delete=models.PROTECT,
        related_name="timetable_entries",
    )
    faculty = models.ForeignKey(
        "accounts.User",
        on_delete=models.PROTECT,
        limit_choices_to={"role": "FACULTY"},
        related_name="timetable_entries",
    )
    weekday = models.CharField(
        max_length=3,
        choices=Weekday.choices,
    )
    classroom = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if not all([
            self.college_id,
            self.academic_year_id,
            self.class_section_id,
            self.period_id,
            self.course_id,
            self.faculty_id,
            self.weekday,
        ]):
            return

        section = self.class_section

        if section.college_id != self.college_id:
            raise ValidationError(
                "Class section must belong to the selected college."
            )

        if self.academic_year.college_id != self.college_id:
            raise ValidationError(
                "Academic year must belong to the selected college."
            )

        if section.academic_year_id != self.academic_year_id:
            raise ValidationError(
                "Academic year must match the class section."
            )

        if self.period.college_id != self.college_id:
            raise ValidationError(
                "Period must belong to the selected college."
            )

        if self.course.college_id != self.college_id:
            raise ValidationError(
                "Course must belong to the selected college."
            )

        if self.course.department_id != section.department_id:
            raise ValidationError(
                "Course and class section must belong to the same department."
            )

        if self.faculty.college_id != self.college_id:
            raise ValidationError(
                "Faculty must belong to the selected college."
            )

        if self.faculty.role != "FACULTY":
            raise ValidationError(
                "Only faculty members can be assigned."
            )

        assigned = FacultyAssignment.objects.filter(
            college=self.college,
            faculty=self.faculty,
            course=self.course,
            class_section=section,
        ).exists()

        if not assigned:
            raise ValidationError(
                "This faculty member is not assigned to the selected course and class."
            )

        # Check faculty timetable conflicts
        faculty_conflict = Timetable.objects.filter(
            college=self.college,
            faculty=self.faculty,
            weekday=self.weekday,
            period=self.period,
            is_active=True,
        ).exclude(pk=self.pk).exists()

        if faculty_conflict:
            raise ValidationError(
                "This faculty member already has a class during this period."
            )

        # Check classroom timetable conflicts
        if self.classroom.strip():
            classroom_conflict = Timetable.objects.filter(
                college=self.college,
                classroom__iexact=self.classroom.strip(),
                weekday=self.weekday,
                period=self.period,
                is_active=True,
            ).exclude(pk=self.pk).exists()

            if classroom_conflict:
                raise ValidationError(
                    "This classroom is already occupied during this period."
                )

    class Meta:
        ordering = ["weekday", "period__number"]
        constraints = [
            models.UniqueConstraint(
                fields=["class_section", "weekday", "period"],
                name="unique_class_period_per_weekday",
            ),
        ]

    def __str__(self):
        return (
            f"{self.class_section} - "
            f"{self.get_weekday_display()} - "
            f"{self.period}"
        )


    