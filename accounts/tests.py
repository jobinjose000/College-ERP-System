
from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory

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
