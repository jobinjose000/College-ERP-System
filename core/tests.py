
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from core.models import College


class CollegeStatusTests(TestCase):
    def setUp(self):
        User = get_user_model()

        self.college = College.objects.create(
            name="Test College",
            code="test-college",
        )

        self.super_admin = User.objects.create_user(
            username="test_super_admin",
            password="TestPass123!",
            role="SUPER_ADMIN",
        )

        self.student = User.objects.create_user(
            username="test_student",
            password="TestPass123!",
            role="STUDENT",
        )

    def test_super_admin_can_deactivate_college(self):
        self.client.force_login(self.super_admin)

        response = self.client.post(
            reverse(
                "college_toggle_status",
                args=[self.college.pk],
            )
        )

        self.college.refresh_from_db()

        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.college.is_active)

    def test_student_cannot_deactivate_college(self):
        self.client.force_login(self.student)

        response = self.client.post(
            reverse(
                "college_toggle_status",
                args=[self.college.pk],
            )
        )

        self.college.refresh_from_db()

        self.assertEqual(response.status_code, 403)
        self.assertTrue(self.college.is_active)

    def test_get_request_cannot_change_college_status(self):
        self.client.force_login(self.super_admin)

        response = self.client.get(
            reverse(
                "college_toggle_status",
                args=[self.college.pk],
            )
        )

        self.college.refresh_from_db()

        self.assertEqual(response.status_code, 405)
        self.assertTrue(self.college.is_active)
