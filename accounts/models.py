from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.


class User(AbstractUser):
    
    ROLE = (
        ('ADMIN' , 'Admin'),
        ('RECRUITER' , 'Recruiter'),
        ('STUDENT' , 'Student'),
    )
    
    role = models.CharField(choices=ROLE , max_length=9 ,default= 'STUDENT')
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0.00)
    backlogs = models.IntegerField(default=0)
    
    def __str__(self):
        return f'{self.username} {self.role}'

