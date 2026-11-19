from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentRoster, StudentProfile, Notification


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



@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'updated_at')
    search_fields = ('user__username', 'user__roll_number', 'user__email')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'category', 'is_read', 'created_at')
    list_filter = ('category', 'is_read')
    search_fields = ('user__username', 'title', 'message')
    readonly_fields = ('created_at',)
