from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
import uuid
from accounts.models import User





class SkillCategory(models.Model):
    """Categories for different types of handyman services"""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)  # FontAwesome or similar icon class
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Skill Categories"

    def __str__(self):
        return self.name


class Skill(models.Model):
    """Individual skills within categories"""
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_name='skills')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ['category', 'name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class WorkerProfile(models.Model):
    """Extended profile for workers with skills and availability"""
    EXPERIENCE_LEVELS = [
        ('BEGINNER', '0-2 years'),
        ('INTERMEDIATE', '2-5 years'),
        ('EXPERIENCED', '5-10 years'),
        ('EXPERT', '10+ years'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="worker_profile")
    bio = models.TextField(max_length=500, blank=True)
    skills = models.ManyToManyField(Skill, through='WorkerSkill', blank=True)
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='BEGINNER')
    hourly_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    rating = models.FloatField(default=0.0, validators=[MinValueValidator(0.0), MaxValueValidator(5.0)])
    num_ratings = models.PositiveIntegerField(default=0)
    total_jobs_completed = models.PositiveIntegerField(default=0)
    is_available = models.BooleanField(default=True)
    background_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def update_rating(self, new_score):
        """Update worker rating with new review score"""
        total = self.rating * self.num_ratings
        total += new_score
        self.num_ratings += 1
        self.rating = total / self.num_ratings
        self.save()

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.get_experience_level_display()}"


class WorkerSkill(models.Model):
    """Through model for worker skills with proficiency levels"""
    PROFICIENCY_LEVELS = [
        ('BASIC', 'Basic'),
        ('INTERMEDIATE', 'Intermediate'),
        ('ADVANCED', 'Advanced'),
        ('EXPERT', 'Expert'),
    ]
    
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    proficiency = models.CharField(max_length=20, choices=PROFICIENCY_LEVELS, default='BASIC')
    years_experience = models.PositiveIntegerField(default=0)
    certified = models.BooleanField(default=False)

    class Meta:
        unique_together = ['worker', 'skill']

    def __str__(self):
        return f"{self.worker.user.get_full_name()} - {self.skill.name} ({self.proficiency})"


class Job(models.Model):
    """Job postings by clients"""
    JOB_STATUS = [
        ('DRAFT', 'Draft'),
        ('OPEN', 'Open'),
        ('ASSIGNED', 'Assigned'),
        ('IN_PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    PRIORITY_LEVELS = [
        ('LOW', 'Low'),
        ('MEDIUM', 'Medium'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs_posted')
    title = models.CharField(max_length=200)
    description = models.TextField()
    required_skills = models.ManyToManyField(Skill, blank=True)
    location = models.CharField(max_length=255, help_text="Location coordinates or address")
    address = models.TextField()
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estimated_duration = models.PositiveIntegerField(help_text="Duration in hours", null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='MEDIUM')
    status = models.CharField(max_length=20, choices=JOB_STATUS, default='DRAFT')
    assigned_worker = models.ForeignKey(WorkerProfile, null=True, blank=True, on_delete=models.SET_NULL)
    scheduled_for = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.client.get_full_name()}"

    @property
    def is_active(self):
        return self.status in ['OPEN', 'ASSIGNED', 'IN_PROGRESS']


class JobApplication(models.Model):
    """Applications from workers for jobs"""
    APPLICATION_STATUS = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='applications')
    cover_letter = models.TextField(blank=True)
    proposed_rate = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_completion = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=APPLICATION_STATUS, default='PENDING')
    applied_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['job', 'worker']

    def __str__(self):
        return f"{self.worker.user.get_full_name()} -> {self.job.title}"


class Rating(models.Model):
    """Rating system for completed jobs"""
    RATING_TYPES = [
        ('CLIENT_TO_WORKER', 'Client to Worker'),
        ('WORKER_TO_CLIENT', 'Worker to Client'),
    ]
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="ratings")
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    ratee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    rating_type = models.CharField(max_length=20, choices=RATING_TYPES)
    stars = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['job', 'rater', 'rating_type']

    def __str__(self):
        return f"{self.stars} stars - {self.job.title}"


class Message(models.Model):
    """Direct messaging between users"""
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_sent')
    receiver = models.ForeignKey(User, on_delete=models.CASCADE, related_name='messages_received')
    job = models.ForeignKey(Job, null=True, blank=True, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"{self.sender.username} -> {self.receiver.username}: {self.content[:50]}"


class Notification(models.Model):
    """Notification system"""
    NOTIFICATION_TYPES = [
        ('JOB_POSTED', 'Job Posted'),
        ('APPLICATION_RECEIVED', 'Application Received'),
        ('APPLICATION_ACCEPTED', 'Application Accepted'),
        ('APPLICATION_REJECTED', 'Application Rejected'),
        ('JOB_STARTED', 'Job Started'),
        ('JOB_COMPLETED', 'Job Completed'),
        ('RATING_RECEIVED', 'Rating Received'),
        ('MESSAGE_RECEIVED', 'Message Received'),
        ('SYSTEM', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPES, default='SYSTEM')
    related_job = models.ForeignKey(Job, null=True, blank=True, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.user.username}"


class WorkerAvailability(models.Model):
    """Worker availability schedule"""
    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]
    
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE, related_name='availability')
    day_of_week = models.PositiveSmallIntegerField(choices=DAYS_OF_WEEK)
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['worker', 'day_of_week']

    def __str__(self):
        return f"{self.worker.user.get_full_name()} - {self.get_day_of_week_display()}"


class AIMatchingScore(models.Model):
    """Store AI matching scores for job-worker pairs"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE)
    worker = models.ForeignKey(WorkerProfile, on_delete=models.CASCADE)
    score = models.FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    factors = models.JSONField(default=dict)  # Store factors that contributed to the score
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['job', 'worker']

    def __str__(self):
        return f"{self.job.title} - {self.worker.user.get_full_name()}: {self.score}"