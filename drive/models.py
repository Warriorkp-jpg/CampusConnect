from django.db import models
from django.conf import settings

class Drive(models.Model):
    company_name = models.CharField(max_length=100)
    role_title = models.CharField(max_length=100)
    package_lpa = models.DecimalField(max_digits=5, decimal_places=2)
    
    
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=6.00)
    max_backlogs = models.IntegerField(default=0)
    
    # Track which Recruiter posted this drive
    posted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posted_drives'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company_name} - {self.role_title}"