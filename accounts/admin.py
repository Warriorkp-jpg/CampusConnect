from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentRoster


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'email', 'role', 'recruiter_status', 'company_name',
        'is_staff', 'is_superuser'
    )
    list_filter = ('role', 'recruiter_status', 'is_staff')
    search_fields = ('username', 'email', 'roll_number', 'company_name')
    fieldsets = UserAdmin.fieldsets + (
        ('CampusConnect Profile', {
            'fields': ('role', 'roll_number', 'recruiter_status', 'company_name',
                       'phone_number', 'cgpa', 'backlogs')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('CampusConnect Profile', {
            'fields': ('role', 'roll_number', 'recruiter_status', 'company_name',
                       'phone_number', 'cgpa', 'backlogs')
        }),
    )


@admin.register(StudentRoster)
class StudentRosterAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'full_name', 'college_email', 'program', 'batch', 'student_user')
    search_fields = ('roll_number', 'full_name', 'college_email')
    list_filter = ('program', 'batch')
