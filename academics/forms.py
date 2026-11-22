
from django import forms

from accounts.models import StudentProfile, User
from .models import (
    AcademicYear,
    ClassSection,
    Enrollment,
    Attendance,
    Period,
    Course,
    FacultyAssignment,
    Timetable,
)


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


class AttendanceDateForm(forms.Form):

    date = forms.DateField(
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": "form-control",
            }
        )
    )


class TimetableForm(forms.ModelForm):

    class Meta:
        model = Timetable
        fields = [
            "academic_year",
            "class_section",
            "period",
            "course",
            "faculty",
            "weekday",
            "classroom",
            "is_active",
        ]

        widgets = {
            "weekday": forms.Select(
                attrs={"class": "form-select"}
            ),
            "classroom": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Room 101",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None:
            raise ValueError("A logged-in user is required.")

        self.user = user

        self.fields["academic_year"].queryset = (
            AcademicYear.objects.filter(college=user.college)
        )

        self.fields["class_section"].queryset = (
            ClassSection.objects.filter(college=user.college)
        )

        self.fields["period"].queryset = (
            Period.objects.filter(
                college=user.college,
                is_active=True,
            )
        )

        self.fields["course"].queryset = (
            Course.objects.filter(college=user.college)
        )

        self.fields["faculty"].queryset = (
            User.objects.filter(
                college=user.college,
                role=User.Role.FACULTY,
                is_active=True,
            ).order_by("username")
        )

    def save(self, commit=True):
        timetable = super().save(commit=False)
        timetable.college = self.user.college

        if commit:
            timetable.full_clean()
            timetable.save()

        return timetable
