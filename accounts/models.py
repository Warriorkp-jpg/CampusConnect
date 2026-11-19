from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


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

    role = models.CharField(max_length=9, choices=ROLE_CHOICES, default='STUDENT')
    roll_number = models.CharField(max_length=30, unique=True, null=True, blank=True)
    recruiter_status = models.CharField(
        max_length=20, choices=RECRUITER_STATUS_CHOICES, default='NOT_REQUIRED'
    )
    company_name = models.CharField(max_length=150, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    backlogs = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.username} ({self.role})'


class StudentRoster(models.Model):
    """College-approved student record used to verify student registration."""
    roll_number = models.CharField(max_length=30, unique=True)
    full_name = models.CharField(max_length=150)
    college_email = models.EmailField(blank=True)
    program = models.CharField(max_length=100, default='B.Tech CSE')
    batch = models.CharField(max_length=20, blank=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    backlogs = models.PositiveIntegerField(default=0)
    student_user = models.OneToOneField(
        'accounts.User', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='roster_record'
    )
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.roll_number} - {self.full_name}'


class StudentEmailOTP(models.Model):
    """Short-lived, hashed email verification challenge for student onboarding."""
    challenge_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    roll_number = models.CharField(max_length=30, db_index=True)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    verified_at = models.DateTimeField(null=True, blank=True)
    consumed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['roll_number', 'created_at'], name='accounts_st_roll_n_7d3c1a_idx'),
            models.Index(fields=['challenge_id', 'expires_at'], name='accounts_st_challe_7a0a44_idx'),
        ]

    def __str__(self):
        return f'Student email verification for {self.roll_number}'
