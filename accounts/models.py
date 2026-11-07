from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = (
        ('TPO', 'Training and Placement Officer'),
        ('RECRUITER', 'Recruiter'),
        ('STUDENT', 'Student'),
    )

    RECRUITER_STATUS_CHOICES = (
        ('NOT_REQUIRED', 'Not required'),
        ('PENDING', 'Pending approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    )

    role = models.CharField(
        max_length=9,
        choices=ROLE_CHOICES,
        default='STUDENT',
    )

    # JMIT roll number is the student's login identifier.
    # It is nullable because recruiter and TPO accounts do not have one.
    roll_number = models.CharField(
        max_length=30,
        unique=True,
        null=True,
        blank=True,
    )

    # Recruiters remain pending until a TPO approves their account.
    # This status is NOT a substitute for the role permission check.
    recruiter_status = models.CharField(
        max_length=20,
        choices=RECRUITER_STATUS_CHOICES,
        default='NOT_REQUIRED',
    )

    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    backlogs = models.IntegerField(default=0)

    def __str__(self):
        return f'{self.username} ({self.role})'
