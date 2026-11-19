
from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import StudentProfile, User
from core.models import College

from .forms import EnrollmentForm
from .models import (
    AcademicYear,
    ClassSection,
    Course,
    Department,
    Enrollment,
    FacultyAssignment,
)


class EnrollmentFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.college = College.objects.create(
            name="ABC College of Engineering",
            code="abc-college",
            email="abc@example.com",
            address="Kollam",
        )

        cls.college_admin = User.objects.create_user(
            username="college_admin_test",
            password="testpassword123",
            role=User.Role.COLLEGE_ADMIN,
            college=cls.college,
        )

        cls.student_user = User.objects.create_user(
            username="student_test",
            password="testpassword123",
            role=User.Role.STUDENT,
            college=cls.college,
        )

        cls.student = StudentProfile.objects.create(
            user=cls.student_user,
            registration_number="TEST001",
            department="Computer Science",
            admission_year=2026,
        )

        cls.academic_year = AcademicYear.objects.create(
            college=cls.college,
            name="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31),
            is_active=True,
        )

        cls.department = Department.objects.create(
            college=cls.college,
            name="Computer Science",
            code="CSE",
        )

        cls.class_section = ClassSection.objects.create(
            college=cls.college,
            academic_year=cls.academic_year,
            department=cls.department,
            name="A",
            semester=5,
        )

        cls.other_college = College.objects.create(
            name="XYZ Engineering College",
            code="xyz-college",
            email="xyz@example.com",
            address="Kochi",
        )

        cls.other_student_user = User.objects.create_user(
            username="other_student_test",
            password="testpassword123",
            role=User.Role.STUDENT,
            college=cls.other_college,
        )

        cls.other_student = StudentProfile.objects.create(
            user=cls.other_student_user,
            registration_number="XYZ001",
            department="Computer Science",
            admission_year=2026,
        )

        cls.other_academic_year = AcademicYear.objects.create(
            college=cls.other_college,
            name="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31),
            is_active=True,
        )

        cls.other_department = Department.objects.create(
            college=cls.other_college,
            name="Computer Science",
            code="CSE",
        )

        cls.other_class_section = ClassSection.objects.create(
            college=cls.other_college,
            academic_year=cls.other_academic_year,
            department=cls.other_department,
            name="A",
            semester=5,
        )

    def test_valid_student_enrollment(self):

        form = EnrollmentForm(
            data={
                "student": self.student.pk,
                "academic_year": self.academic_year.pk,
                "class_section": self.class_section.pk,
                "is_active": True,
            },
            user=self.college_admin,
        )

        self.assertTrue(form.is_valid(), form.errors)

        enrollment = form.save()

        self.assertEqual(enrollment.student, self.student)
        self.assertEqual(
            enrollment.class_section,
            self.class_section,
        )

    def test_college_admin_can_only_see_own_college_records(self):

        form = EnrollmentForm(user=self.college_admin)

        student_ids = list(
            form.fields["student"].queryset.values_list(
                "id",
                flat=True,
            )
        )

        academic_year_ids = list(
            form.fields["academic_year"].queryset.values_list(
                "id",
                flat=True,
            )
        )

        class_section_ids = list(
            form.fields["class_section"].queryset.values_list(
                "id",
                flat=True,
            )
        )

        self.assertIn(self.student.pk, student_ids)
        self.assertNotIn(self.other_student.pk, student_ids)

        self.assertIn(self.academic_year.pk, academic_year_ids)
        self.assertNotIn(
            self.other_academic_year.pk,
            academic_year_ids,
        )

        self.assertIn(self.class_section.pk, class_section_ids)
        self.assertNotIn(
            self.other_class_section.pk,
            class_section_ids,
        )

    def test_college_admin_cannot_enroll_other_college_student(self):

        form = EnrollmentForm(
            data={
                "student": self.other_student.pk,
                "academic_year": self.academic_year.pk,
                "class_section": self.class_section.pk,
                "is_active": True,
            },
            user=self.college_admin,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("student", form.errors)


class FacultyAssignedStudentsTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        cls.college = College.objects.create(
            name="ABC College of Engineering",
            code="faculty-test-college",
            email="faculty@example.com",
            address="Kollam",
        )

        cls.faculty = User.objects.create_user(
            username="faculty_test",
            password="testpassword123",
            role=User.Role.FACULTY,
            college=cls.college,
        )

        cls.another_faculty = User.objects.create_user(
            username="another_faculty",
            password="testpassword123",
            role=User.Role.FACULTY,
            college=cls.college,
        )

        cls.student_user = User.objects.create_user(
            username="faculty_student",
            password="testpassword123",
            role=User.Role.STUDENT,
            college=cls.college,
        )

        cls.student = StudentProfile.objects.create(
            user=cls.student_user,
            registration_number="FACST001",
            department="Computer Science",
            admission_year=2026,
        )

        cls.academic_year = AcademicYear.objects.create(
            college=cls.college,
            name="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31),
            is_active=True,
        )

        cls.department = Department.objects.create(
            college=cls.college,
            name="Computer Science",
            code="FAC-CSE",
        )

        cls.class_section = ClassSection.objects.create(
            college=cls.college,
            academic_year=cls.academic_year,
            department=cls.department,
            name="A",
            semester=5,
        )

        cls.course = Course.objects.create(
            college=cls.college,
            department=cls.department,
            code="FAC-CS301",
            name="Database Management Systems",
            credits=3,
            semester=5,
        )

        cls.assignment = FacultyAssignment.objects.create(
            college=cls.college,
            faculty=cls.faculty,
            course=cls.course,
            class_section=cls.class_section,
        )

    def test_faculty_can_view_students_in_assigned_class(self):

        Enrollment.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            class_section=self.class_section,
            is_active=True,
        )

        self.client.force_login(self.faculty)

        url = reverse(
            "assigned_class_students",
            kwargs={"assignment_id": self.assignment.pk},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "FACST001")
        self.assertContains(response, "faculty_student")

    def test_faculty_cannot_view_another_facultys_assignment(self):

        another_assignment = FacultyAssignment.objects.create(
            college=self.college,
            faculty=self.another_faculty,
            course=self.course,
            class_section=self.class_section,
        )

        self.client.force_login(self.faculty)

        url = reverse(
            "assigned_class_students",
            kwargs={"assignment_id": another_assignment.pk},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_inactive_enrollments_are_not_displayed(self):

        Enrollment.objects.create(
            student=self.student,
            academic_year=self.academic_year,
            class_section=self.class_section,
            is_active=False,
        )

        self.client.force_login(self.faculty)

        url = reverse(
            "assigned_class_students",
            kwargs={"assignment_id": self.assignment.pk},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "FACST001")

    def test_students_from_other_colleges_are_not_displayed(self):

        other_college_student_user = User.objects.create_user(
            username="foreign_student",
            password="testpassword123",
            role=User.Role.STUDENT,
            college=College.objects.create(
                name="XYZ Engineering College",
                code="faculty-other-college",
                email="xyz-faculty@example.com",
                address="Kochi",
            ),
        )

        other_college_student = StudentProfile.objects.create(
            user=other_college_student_user,
            registration_number="FOREIGN001",
            department="Computer Science",
            admission_year=2026,
        )

        # Create an inconsistent enrollment directly to test
        # whether the faculty view still protects college isolation.
        Enrollment.objects.create(
            student=other_college_student,
            academic_year=self.academic_year,
            class_section=self.class_section,
            is_active=True,
        )

        self.client.force_login(self.faculty)

        url = reverse(
            "assigned_class_students",
            kwargs={"assignment_id": self.assignment.pk},
        )

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "FOREIGN001")
