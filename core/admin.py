from django.contrib import admin
from .models import (
    SkillCategory, Skill, WorkerProfile, WorkerSkill, Job, JobApplication,
    Rating, Message, Notification, WorkerAvailability, AIMatchingScore
)

# Register your models here.

@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)
    list_editable = ('is_active',)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('name', 'description', 'category__name')
    ordering = ('category__name', 'name')
    list_editable = ('is_active',)


class WorkerSkillInline(admin.TabularInline):
    model = WorkerSkill
    extra = 1
    autocomplete_fields = ('skill',)


class WorkerAvailabilityInline(admin.TabularInline):
    model = WorkerAvailability
    extra = 1


@admin.register(WorkerProfile)
class WorkerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'experience_level', 'hourly_rate', 'rating', 'num_ratings', 'total_jobs_completed', 'is_available', 'background_verified')
    list_filter = ('experience_level', 'is_available', 'background_verified', 'created_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name', 'bio')
    ordering = ('-created_at',)
    list_editable = ('is_available', 'background_verified')
    readonly_fields = ('rating', 'num_ratings', 'total_jobs_completed', 'created_at', 'updated_at')
    inlines = [WorkerSkillInline, WorkerAvailabilityInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'bio', 'experience_level', 'hourly_rate')
        }),
        ('Status & Verification', {
            'fields': ('is_available', 'background_verified')
        }),
        ('Statistics', {
            'fields': ('rating', 'num_ratings', 'total_jobs_completed'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkerSkill)
class WorkerSkillAdmin(admin.ModelAdmin):
    list_display = ('worker', 'skill', 'proficiency', 'years_experience', 'certified')
    list_filter = ('proficiency', 'certified', 'skill__category')
    search_fields = ('worker__user__username', 'worker__user__first_name', 'worker__user__last_name', 'skill__name')
    ordering = ('worker__user__first_name', 'skill__name')
    list_editable = ('proficiency', 'years_experience', 'certified')
    autocomplete_fields = ('worker', 'skill')


class JobApplicationInline(admin.TabularInline):
    model = JobApplication
    extra = 0
    readonly_fields = ('applied_at',)
    fields = ('worker', 'status', 'proposed_rate', 'applied_at')


class RatingInline(admin.TabularInline):
    model = Rating
    extra = 0
    readonly_fields = ('created_at',)
    fields = ('rater', 'ratee', 'rating_type', 'stars', 'comment', 'created_at')


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ('title', 'client', 'status', 'priority', 'budget_min', 'budget_max', 'assigned_worker', 'created_at')
    list_filter = ('status', 'priority', 'created_at', 'scheduled_for')
    search_fields = ('title', 'description', 'client__username', 'client__first_name', 'client__last_name', 'location')
    ordering = ('-created_at',)
    list_editable = ('status', 'priority')
    readonly_fields = ('id', 'created_at', 'updated_at')
    autocomplete_fields = ('client', 'assigned_worker', 'required_skills')
    inlines = [JobApplicationInline, RatingInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'client', 'title', 'description', 'required_skills')
        }),
        ('Location & Budget', {
            'fields': ('location', 'address', 'budget_min', 'budget_max')
        }),
        ('Job Details', {
            'fields': ('priority', 'status', 'estimated_duration', 'scheduled_for')
        }),
        ('Assignment', {
            'fields': ('assigned_worker', 'started_at', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ('job', 'worker', 'status', 'proposed_rate', 'applied_at', 'responded_at')
    list_filter = ('status', 'applied_at', 'responded_at')
    search_fields = ('job__title', 'worker__user__username', 'worker__user__first_name', 'worker__user__last_name')
    ordering = ('-applied_at',)
    list_editable = ('status',)
    readonly_fields = ('applied_at', 'responded_at')
    autocomplete_fields = ('job', 'worker')
    
    fieldsets = (
        ('Application Details', {
            'fields': ('job', 'worker', 'cover_letter', 'proposed_rate', 'estimated_completion')
        }),
        ('Status', {
            'fields': ('status', 'responded_at')
        }),
        ('Timestamps', {
            'fields': ('applied_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('job', 'rater', 'ratee', 'rating_type', 'stars', 'created_at')
    list_filter = ('rating_type', 'stars', 'created_at')
    search_fields = ('job__title', 'rater__username', 'ratee__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)
    autocomplete_fields = ('job', 'rater', 'ratee')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'receiver', 'job', 'read', 'timestamp')
    list_filter = ('read', 'timestamp', 'job')
    search_fields = ('sender__username', 'receiver__username', 'content', 'job__title')
    ordering = ('-timestamp',)
    list_editable = ('read',)
    readonly_fields = ('timestamp', 'read_at')
    autocomplete_fields = ('sender', 'receiver', 'job')
    
    fieldsets = (
        ('Message Details', {
            'fields': ('sender', 'receiver', 'job', 'content')
        }),
        ('Status', {
            'fields': ('read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('timestamp',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'read', 'created_at')
    list_filter = ('notification_type', 'read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    ordering = ('-created_at',)
    list_editable = ('read',)
    readonly_fields = ('created_at', 'read_at')
    autocomplete_fields = ('user', 'related_job')
    
    fieldsets = (
        ('Notification Details', {
            'fields': ('user', 'title', 'message', 'notification_type', 'related_job')
        }),
        ('Status', {
            'fields': ('read', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(WorkerAvailability)
class WorkerAvailabilityAdmin(admin.ModelAdmin):
    list_display = ('worker', 'day_of_week', 'start_time', 'end_time', 'is_available')
    list_filter = ('day_of_week', 'is_available')
    search_fields = ('worker__user__username', 'worker__user__first_name', 'worker__user__last_name')
    ordering = ('worker__user__first_name', 'day_of_week')
    list_editable = ('start_time', 'end_time', 'is_available')
    autocomplete_fields = ('worker',)


@admin.register(AIMatchingScore)
class AIMatchingScoreAdmin(admin.ModelAdmin):
    list_display = ('job', 'worker', 'score', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('job__title', 'worker__user__username', 'worker__user__first_name', 'worker__user__last_name')
    ordering = ('-score', '-created_at')
    readonly_fields = ('created_at',)
    autocomplete_fields = ('job', 'worker')
    
    fieldsets = (
        ('Matching Details', {
            'fields': ('job', 'worker', 'score', 'factors')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
