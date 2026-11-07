from django.db import models
from django.conf import settings
from django.utils import timezone


class Drive(models.Model):
    company_name = models.CharField(max_length=100)
    role_title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=150, blank=True)
    package_lpa = models.DecimalField(max_digits=5, decimal_places=2)
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=6.00)
    max_backlogs = models.PositiveIntegerField(default=0)
    application_deadline = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='posted_drives'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_open(self):
        recruiter_is_valid = (
            self.posted_by.role == 'TPO' or (
                self.posted_by.role == 'RECRUITER'
                and self.posted_by.recruiter_status == 'APPROVED'
            )
        )
        return self.is_active and recruiter_is_valid and (
            self.application_deadline is None or self.application_deadline >= timezone.now()
        )

    def __str__(self):
        return f'{self.company_name} - {self.role_title}'
