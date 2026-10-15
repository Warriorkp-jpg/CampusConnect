from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    # Show the 'role' column in the admin user list table
    list_display = ('username', 'email', 'role', 'is_staff', 'is_superuser')
    
    # Allow editing the 'role' field when clicking on a user in the admin panel
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )

admin.site.register(User, CustomUserAdmin)