from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class Location(models.Model):
    """Public Administration Center Location"""
    name = models.CharField(max_length=200, unique=True)
    address = models.TextField()
    state = models.CharField(max_length=100)
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} - {self.state}"


class User(AbstractUser):
    """Custom User Model"""
    ROLE_CHOICES = [
        ('admin', 'Location Admin'),
        ('staff', 'Staff Member'),
        ('superadmin', 'Super Administrator'),
    ]
    
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users'
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='staff'
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$')]
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    def get_accessible_locations(self):
        """Get all locations this user can access"""
        if self.role == 'superadmin':
            return Location.objects.filter(active=True)
        return Location.objects.filter(id=self.location.id, active=True)