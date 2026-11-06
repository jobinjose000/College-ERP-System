from django import forms

from accounts.models import StudentProfile
from .models import AcademicYear, ClassSection, Enrollment


class EnrollmentForm(forms.ModelForm):

    class Meta:
        model = Enrollment
        fields = [
            "student",
            "academic_year",
            "class_section",
            "is_active",
        ]

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None:
            raise ValueError("A logged-in user is required.")

        if user.role == "SUPER_ADMIN":
            self.fields["student"].queryset = (
                StudentProfile.objects
                .select_related("user")
                .order_by("registration_number")
            )

            self.fields["academic_year"].queryset = (
                AcademicYear.objects.all()
            )

            self.fields["class_section"].queryset = (
                ClassSection.objects.all()
            )

        else:
            self.fields["student"].queryset = (
                StudentProfile.objects
                .filter(user__college=user.college)
                .select_related("user")
                .order_by("registration_number")
            )

            self.fields["academic_year"].queryset = (
                AcademicYear.objects
                .filter(college=user.college)
            )

            self.fields["class_section"].queryset = (
                ClassSection.objects
                .filter(college=user.college)
            )