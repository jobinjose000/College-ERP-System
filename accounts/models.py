
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):

    class Role(models.TextChoices):
        SUPER_ADMIN = "SUPER_ADMIN", "Super Admin"
        COLLEGE_ADMIN = "COLLEGE_ADMIN", "College Admin"
        FACULTY = "FACULTY", "Faculty"
        STUDENT = "STUDENT", "Student"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    college = models.ForeignKey(
        "core.College",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="users",
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class StudentProfile(models.Model):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    registration_number = models.CharField(
        max_length=30,
        unique=True,
    )
    department = models.CharField(max_length=100)
    admission_year = models.PositiveSmallIntegerField()
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.registration_number} - {self.user.username}"


class FacultyProfile(models.Model):
    user = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="faculty_profile",
    )
    employee_id = models.CharField(max_length=30, unique=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.employee_id} - {self.user.username}"
