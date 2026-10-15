from django.db import models
from django.conf import settings
from drive.models import Drive


class Application(models.Model):
    STATUS_CHOICES = (
        ('APPLIED', 'Applied'),
        ('SHORTLISTED', 'Shortlisted'),
        ('REJECTED', 'Rejected'),
        ('SELECTED', 'Selected'),
    )

    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    drive = models.ForeignKey(
        Drive,
        on_delete=models.CASCADE,
        related_name='applications'
    )
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='APPLIED'
    )
    applied_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Prevent the same student from applying to the same drive twice at the DB level!
        unique_together = ('student', 'drive')

    def __str__(self):
        return f"{self.student.username} -> {self.drive.company_name}"