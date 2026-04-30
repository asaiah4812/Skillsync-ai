from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

# Create your models here.

class User(AbstractUser):
    """Extended User model with role-based access"""
    USER_TYPES = [
        ('CLIENT', 'Client'),
        ('WORKER', 'Worker'),
        ('ADMIN', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='CLIENT')
    phone = models.CharField(max_length=20, blank=True, null=True)
    matriculation_number = models.CharField(max_length=30, unique=True, blank=True, null=True)
    expected_graduation_year = models.PositiveSmallIntegerField(blank=True, null=True)
    profile_picture = models.ImageField(upload_to='profiles/', blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True, help_text="Location coordinates or address")
    address = models.TextField(blank=True)
    is_verified = models.BooleanField(default=False)
    has_listed_skill = models.BooleanField(
        default=False,
        help_text="True when the student has listed at least one skill."
    )
    subscription_active = models.BooleanField(
        default=False,
        help_text="True when learner access subscription is active."
    )
    subscription_expires_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} - {self.get_user_type_display()}"