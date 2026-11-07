from django.contrib import admin
from .models import Drive


@admin.register(Drive)
class DriveAdmin(admin.ModelAdmin):
    list_display = ('company_name', 'role_title', 'package_lpa', 'is_active', 'application_deadline', 'posted_by')
    list_filter = ('is_active', 'created_at')
    search_fields = ('company_name', 'role_title', 'posted_by__username')
