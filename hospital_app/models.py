from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        
    ]
    
    name=models.CharField(max_length=50,blank=True)
    phone = models.CharField(max_length=15, blank=True)
    age = models.IntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=[('Male','Male'), ('Female','Female'), ('Other','Other')], blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    speciality=models.CharField(max_length=100,blank=True,null=True)


    def __str__(self):
        return f"{self.name} ({self.role})"
    
    class Meta:
        swappable = 'AUTH_USER_MODEL'



class Appointment(models.Model):
    STATUS_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_appointments')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_appointments')
    date = models.DateField(default=timezone.now)  #  combined date + time
    time=models.TimeField(default="12:00")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='approved')

    booked_at = models.DateTimeField(auto_now_add=True,null=True, blank=True)

    def __str__(self):
        return f"{self.patient.username} with {self.doctor.username} at {self.date}"
    
    class Meta:
        unique_together = ('doctor', 'date', 'time')  
        ordering = ['-booked_at'] 
