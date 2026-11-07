from django.contrib import admin
from .models import Application


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('student', 'drive', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('student__username', 'student__roll_number', 'drive__company_name')
    readonly_fields = ('student', 'drive', 'applied_at')
