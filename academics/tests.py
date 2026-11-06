
from datetime import date

from django.test import TestCase

from accounts.models import StudentProfile, User
from core.models import College

from .forms import EnrollmentForm
from .models import AcademicYear, ClassSection, Department


class EnrollmentFormTests(TestCase):

    @classmethod
    def setUpTestData(cls):

        # Create the first college
        cls.college = College.objects.create(
            name="ABC College of Engineering",
            code="abc-college",
            email="abc@example.com",
            address="Kollam",
        )

        # Create a College Admin
        cls.college_admin = User.objects.create_user(
            username="college_admin_test",
            password="testpassword123",
            role=User.Role.COLLEGE_ADMIN,
            college=cls.college,
        )

        # Create a student
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

        # Create academic year
        cls.academic_year = AcademicYear.objects.create(
            college=cls.college,
            name="2026-2027",
            start_date=date(2026, 6, 1),
            end_date=date(2027, 5, 31),
            is_active=True,
        )

        # Create department
        cls.department = Department.objects.create(
            college=cls.college,
            name="Computer Science",
            code="CSE",
        )

        # Create class section
        cls.class_section = ClassSection.objects.create(
            college=cls.college,
            academic_year=cls.academic_year,
            department=cls.department,
            name="A",
            semester=5,
        )

        # Create another college
        cls.other_college = College.objects.create(
            name="XYZ Engineering College",
            code="xyz-college",
            email="xyz@example.com",
            address="Kochi",
        )

        # Create a student in the other college
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
