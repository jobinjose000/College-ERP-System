
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model

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