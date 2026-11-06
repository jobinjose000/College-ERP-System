
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


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
