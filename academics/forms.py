
from django import forms

from accounts.models import StudentProfile, User
from .models import (
    Department,
    AcademicYear,
    ClassSection,
    Enrollment,
    Attendance,
    Period,
    Course,
    FacultyAssignment,
    Timetable,
)


class DepartmentForm(forms.ModelForm):

    class Meta:
        model = Department
        fields = [
            "name",
            "code",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Computer Science",
                }
            ),
            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: CSE",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None or user.college is None:
            raise ValueError(
                "A College Admin account is required."
            )

        self.user = user

    def save(self, commit=True):
        department = super().save(commit=False)
        department.college = self.user.college

        if commit:
            department.full_clean()
            department.save()

        return department


# ==========================================
# COURSE MANAGEMENT FORM
# ==========================================

class CourseForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = [
            "code",
            "name",
            "department",
            "credits",
            "semester",
            "is_active",
        ]

        widgets = {
            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: CS301",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Database Management Systems",
                }
            ),
            "department": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "credits": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 20,
                }
            ),
            "semester": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                    "max": 12,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None or user.college is None:
            raise ValueError(
                "A College Admin account is required."
            )

        self.user = user

        # College Admin can select only their own departments.
        self.fields["department"].queryset = (
            Department.objects.filter(
                college=user.college
            ).order_by("name")
        )

    def save(self, commit=True):
        course = super().save(commit=False)
        course.college = self.user.college

        if commit:
            course.full_clean()
            course.save()

        return course


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


class AcademicYearForm(forms.ModelForm):

    class Meta:
        model = AcademicYear
        fields = [
            "name",
            "start_date",
            "end_date",
            "is_active",
        ]

        widgets = {
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: 2027-2028",
                }
            ),
            "start_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "end_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "form-control",
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={
                    "class": "form-check-input",
                }
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None or user.college is None:
            raise ValueError(
                "A College Admin account is required."
            )

        self.user = user

    def save(self, commit=True):
        academic_year = super().save(commit=False)
        academic_year.college = self.user.college

        if commit:
            academic_year.full_clean()
            academic_year.save()

        return academic_year


class CourseForm(forms.ModelForm):

    class Meta:
        model = Course
        fields = [
            "department",
            "code",
            "name",
            "credits",
            "semester",
            "is_active",
        ]

        widgets = {
            "department": forms.Select(
                attrs={"class": "form-select"}
            ),
            "code": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: CS301",
                }
            ),
            "name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Example: Database Management Systems",
                }
            ),
            "credits": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),
            "semester": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "min": 1,
                }
            ),
            "is_active": forms.CheckboxInput(
                attrs={"class": "form-check-input"}
            ),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user is None or user.college is None:
            raise ValueError(
                "A College Admin account is required."
            )

        self.user = user

        self.fields["department"].queryset = (
            Department.objects.filter(
                college=user.college
            ).order_by("name")
        )

    def save(self, commit=True):
        course = super().save(commit=False)
        course.college = self.user.college

        if commit:
            course.full_clean()
            course.save()

        return course
