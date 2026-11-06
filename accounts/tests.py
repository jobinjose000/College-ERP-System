
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from accounts.models import StudentProfile, FacultyProfile
from accounts.models import User
from accounts.permissions import (
    is_same_college_or_super_admin,
    role_required,
)
from core.models import College


class CollegePermissionTests(TestCase):
    def setUp(self):
        self.college_a = College.objects.create(
            name="ABC College",
            code="abc-college",
        )

        self.college_b = College.objects.create(
            name="XYZ College",
            code="xyz-college",
        )

        self.super_admin = User.objects.create_user(
            username="platform_admin",
            password="test-password-123",
            role=User.Role.SUPER_ADMIN,
        )

        self.college_admin_a = User.objects.create_user(
            username="admin_abc",
            password="test-password-123",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college_a,
        )

        self.student_a = User.objects.create_user(
            username="student_abc",
            password="test-password-123",
            role=User.Role.STUDENT,
            college=self.college_a,
        )

    def test_college_admin_can_access_own_college(self):
        self.assertTrue(
            is_same_college_or_super_admin(
                self.college_admin_a,
                self.college_a,
            )
        )

    def test_college_admin_cannot_access_another_college(self):
        self.assertFalse(
            is_same_college_or_super_admin(
                self.college_admin_a,
                self.college_b,
            )
        )

    def test_super_admin_can_access_multiple_colleges(self):
        self.assertTrue(
            is_same_college_or_super_admin(
                self.super_admin,
                self.college_a,
            )
        )

        self.assertTrue(
            is_same_college_or_super_admin(
                self.super_admin,
                self.college_b,
            )
        )

    def test_student_without_college_cannot_access_college(self):
        student_without_college = User.objects.create_user(
            username="student_no_college",
            password="test-password-123",
            role=User.Role.STUDENT,
        )

        self.assertFalse(
            is_same_college_or_super_admin(
                student_without_college,
                self.college_a,
            )
        )

    def test_role_required_allows_authorized_role(self):
        @role_required(User.Role.COLLEGE_ADMIN)
        def protected_view(request):
            return "Access granted"

        request = RequestFactory().get("/")
        request.user = self.college_admin_a

        self.assertEqual(
            protected_view(request),
            "Access granted",
        )

    def test_role_required_rejects_unauthorized_role(self):
        @role_required(User.Role.COLLEGE_ADMIN)
        def protected_view(request):
            return "Access granted"

        request = RequestFactory().get("/")
        request.user = self.student_a

        with self.assertRaises(PermissionDenied):
            protected_view(request)

class DashboardAccessTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.super_admin = User.objects.create_user(
            username="dashboard_admin",
            password="TestPass123!",
            role="SUPER_ADMIN",
            is_staff=True,
        )

        self.student = User.objects.create_user(
            username="dashboard_student",
            password="TestPass123!",
            role="STUDENT",
        )

        self.faculty = User.objects.create_user(
            username="dashboard_faculty",
            password="TestPass123!",
            role="FACULTY",
        )

    def test_super_admin_can_access_super_admin_dashboard(self):
        self.client.force_login(self.super_admin)

        response = self.client.get(
            reverse("super_admin_dashboard")
        )

        self.assertEqual(response.status_code, 200)

    def test_student_cannot_access_super_admin_dashboard(self):
        self.client.force_login(self.student)

        response = self.client.get(
            reverse("super_admin_dashboard")
        )

        self.assertEqual(response.status_code, 403)

    def test_faculty_cannot_access_college_admin_dashboard(self):
        self.client.force_login(self.faculty)

        response = self.client.get(
            reverse("college_admin_dashboard")
        )

        self.assertEqual(response.status_code, 403)

    def test_unauthenticated_user_is_redirected_to_login(self):
        response = self.client.get(
            reverse("super_admin_dashboard")
        )

        self.assertEqual(response.status_code, 302)

    
class UserManagementIsolationTests(TestCase):
    def setUp(self):
        self.college_a = College.objects.create(
            name="ABC Test College",
            code="abc-test-college",
        )
        self.college_b = College.objects.create(
            name="XYZ Test College",
            code="xyz-test-college",
        )

        self.college_admin = User.objects.create_user(
            username="college_admin_test",
            password="TestPass123!",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college_a,
        )

        self.student_a = User.objects.create_user(
            username="student_a_test",
            password="TestPass123!",
            role=User.Role.STUDENT,
            college=self.college_a,
        )

        self.student_b = User.objects.create_user(
            username="student_b_test",
            password="TestPass123!",
            role=User.Role.STUDENT,
            college=self.college_b,
        )

    def test_college_admin_sees_only_own_college_users(self):
        self.client.force_login(self.college_admin)

        response = self.client.get(reverse("user_list"))

        self.assertEqual(response.status_code, 200)

        usernames = {
            user.username for user in response.context["users"]
        }

        self.assertIn("college_admin_test", usernames)
        self.assertIn("student_a_test", usernames)
        self.assertNotIn("student_b_test", usernames)

    def test_college_admin_cannot_edit_other_college_user(self):
        self.client.force_login(self.college_admin)

        response = self.client.get(
            reverse("user_edit", args=[self.student_b.pk]),
            raise_request_exception=False,
        )

        self.assertEqual(response.status_code, 403)

    def test_college_admin_cannot_create_super_admin(self):
        self.client.force_login(self.college_admin)

        response = self.client.post(
            reverse("user_create"),
            {
                "username": "unauthorized_super_admin",
                "password": "TestPass123!",
                "first_name": "Unauthorized",
                "last_name": "Admin",
                "email": "unauthorized@example.com",
                "role": User.Role.SUPER_ADMIN,
                "college": "",
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            User.objects.filter(
                username="unauthorized_super_admin"
            ).exists()
        )

    def test_college_admin_cannot_move_user_to_another_college(self):
        self.client.force_login(self.college_admin)

        response = self.client.post(
            reverse("user_create"),
            {
                "username": "new_student_test",
                "password": "TestPass123!",
                "first_name": "New",
                "last_name": "Student",
                "email": "newstudent@example.com",
                "role": User.Role.STUDENT,
                "college": str(self.college_b.pk),
                "is_active": "on",
            },
        )

        self.assertEqual(response.status_code, 302)

        new_student = User.objects.get(
            username="new_student_test"
        )

        self.assertEqual(
            new_student.college_id,
            self.college_a.pk,
        )


class StudentManagementTests(TestCase):
    def setUp(self):
        self.college_a = College.objects.create(
            name="Student Test College A",
            code="student-test-a",
        )
        self.college_b = College.objects.create(
            name="Student Test College B",
            code="student-test-b",
        )

        self.super_admin = User.objects.create_user(
            username="student_platform_admin",
            password="TestPass123!",
            role=User.Role.SUPER_ADMIN,
        )

        self.college_admin = User.objects.create_user(
            username="student_college_admin",
            password="TestPass123!",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college_a,
        )

        self.student_a = User.objects.create_user(
            username="student_in_college_a",
            password="TestPass123!",
            role=User.Role.STUDENT,
            college=self.college_a,
        )
        self.profile_a = StudentProfile.objects.create(
            user=self.student_a,
            registration_number="REG-TEST-001",
            department="Computer Science",
            admission_year=2026,
        )

        self.student_b = User.objects.create_user(
            username="student_in_college_b",
            password="TestPass123!",
            role=User.Role.STUDENT,
            college=self.college_b,
        )
        self.profile_b = StudentProfile.objects.create(
            user=self.student_b,
            registration_number="REG-TEST-002",
            department="Electronics",
            admission_year=2026,
        )

    def test_super_admin_can_view_students_from_all_colleges(self):
        self.client.force_login(self.super_admin)

        response = self.client.get(reverse("student_list"))

        self.assertEqual(response.status_code, 200)

        registration_numbers = {
            student.registration_number
            for student in response.context["students"]
        }

        self.assertIn("REG-TEST-001", registration_numbers)
        self.assertIn("REG-TEST-002", registration_numbers)

    def test_college_admin_sees_only_own_college_students(self):
        self.client.force_login(self.college_admin)

        response = self.client.get(reverse("student_list"))

        self.assertEqual(response.status_code, 200)

        registration_numbers = {
            student.registration_number
            for student in response.context["students"]
        }

        self.assertIn("REG-TEST-001", registration_numbers)
        self.assertNotIn("REG-TEST-002", registration_numbers)

    def test_college_admin_cannot_create_student_in_another_college(self):
        self.client.force_login(self.college_admin)

        response = self.client.post(
            reverse("student_create"),
            {
                "username": "spoofed_student",
                "email": "spoofed@example.com",
                "first_name": "Spoofed",
                "last_name": "Student",
                "password": "TestPass123!",
                "registration_number": "REG-SPOOF-001",
                "department": "Computer Science",
                "admission_year": 2026,
                "college_id": str(self.college_b.pk),
            },
        )

        self.assertEqual(response.status_code, 302)

        created_user = User.objects.get(
            username="spoofed_student"
        )

        self.assertEqual(
            created_user.college_id,
            self.college_a.pk,
        )

        self.assertTrue(
            StudentProfile.objects.filter(
                user=created_user,
                registration_number="REG-SPOOF-001",
            ).exists()
        )

    def test_student_cannot_access_student_management(self):
        self.client.force_login(self.student_a)

        list_response = self.client.get(
            reverse("student_list")
        )
        create_response = self.client.get(
            reverse("student_create")
        )

        self.assertEqual(list_response.status_code, 403)
        self.assertEqual(create_response.status_code, 403)


class FacultyManagementTests(TestCase):
    def setUp(self):
        self.college_a = College.objects.create(
            name="Faculty Test College A",
            code="faculty-test-a",
        )

        self.college_b = College.objects.create(
            name="Faculty Test College B",
            code="faculty-test-b",
        )

        self.super_admin = User.objects.create_user(
            username="faculty_platform_admin",
            password="TestPass123!",
            role=User.Role.SUPER_ADMIN,
        )

        self.college_admin = User.objects.create_user(
            username="faculty_college_admin",
            password="TestPass123!",
            role=User.Role.COLLEGE_ADMIN,
            college=self.college_a,
        )

        self.student = User.objects.create_user(
            username="faculty_test_student",
            password="TestPass123!",
            role=User.Role.STUDENT,
            college=self.college_a,
        )

        self.faculty_a = User.objects.create_user(
            username="faculty_a",
            password="TestPass123!",
            role=User.Role.FACULTY,
            college=self.college_a,
        )

        FacultyProfile.objects.create(
            user=self.faculty_a,
            employee_id="FAC-TEST-001",
            department="Computer Science",
            designation="Assistant Professor",
            qualification="M.Tech",
        )

        self.faculty_b = User.objects.create_user(
            username="faculty_b",
            password="TestPass123!",
            role=User.Role.FACULTY,
            college=self.college_b,
        )

        FacultyProfile.objects.create(
            user=self.faculty_b,
            employee_id="FAC-TEST-002",
            department="Electronics",
            designation="Professor",
            qualification="Ph.D.",
        )

    def test_super_admin_can_view_faculty_from_all_colleges(self):
        self.client.force_login(self.super_admin)

        response = self.client.get(reverse("faculty_list"))

        self.assertEqual(response.status_code, 200)

        employee_ids = {
            faculty.employee_id
            for faculty in response.context["faculty_members"]
        }

        self.assertIn("FAC-TEST-001", employee_ids)
        self.assertIn("FAC-TEST-002", employee_ids)

    def test_college_admin_sees_only_own_college_faculty(self):
        self.client.force_login(self.college_admin)

        response = self.client.get(reverse("faculty_list"))

        self.assertEqual(response.status_code, 200)

        employee_ids = {
            faculty.employee_id
            for faculty in response.context["faculty_members"]
        }

        self.assertIn("FAC-TEST-001", employee_ids)
        self.assertNotIn("FAC-TEST-002", employee_ids)

    def test_super_admin_can_create_faculty(self):
        self.client.force_login(self.super_admin)

        response = self.client.post(
            reverse("faculty_create"),
            {
                "username": "new_faculty_admin_test",
                "email": "newfaculty@example.com",
                "first_name": "New",
                "last_name": "Faculty",
                "password": "TestPass123!",
                "employee_id": "FAC-TEST-003",
                "department": "Computer Science",
                "designation": "Assistant Professor",
                "qualification": "M.Tech",
                "phone_number": "9876543210",
                "college_id": str(self.college_a.pk),
            },
        )

        self.assertEqual(response.status_code, 302)

        new_faculty = User.objects.get(
            username="new_faculty_admin_test"
        )

        self.assertEqual(new_faculty.role, User.Role.FACULTY)
        self.assertEqual(new_faculty.college_id, self.college_a.pk)

        self.assertTrue(
            FacultyProfile.objects.filter(
                user=new_faculty,
                employee_id="FAC-TEST-003",
            ).exists()
        )

    def test_college_admin_can_create_faculty_in_own_college(self):
        self.client.force_login(self.college_admin)

        response = self.client.post(
            reverse("faculty_create"),
            {
                "username": "new_faculty_college_test",
                "email": "collegefaculty@example.com",
                "first_name": "College",
                "last_name": "Faculty",
                "password": "TestPass123!",
                "employee_id": "FAC-TEST-004",
                "department": "Mathematics",
                "designation": "Lecturer",
                "qualification": "M.Sc.",
                "phone_number": "9876543211",
                "college_id": str(self.college_b.pk),
            },
        )

        self.assertEqual(response.status_code, 302)

        new_faculty = User.objects.get(
            username="new_faculty_college_test"
        )

        # College Admin must only create faculty in their own college.
        self.assertEqual(new_faculty.role, User.Role.FACULTY)
        self.assertEqual(new_faculty.college_id, self.college_a.pk)

    def test_student_cannot_access_faculty_management(self):
        self.client.force_login(self.student)

        list_response = self.client.get(reverse("faculty_list"))
        create_response = self.client.get(reverse("faculty_create"))

        self.assertEqual(list_response.status_code, 403)
        self.assertEqual(create_response.status_code, 403)
