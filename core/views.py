# core/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Avg, Count, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.utils import timezone
from datetime import datetime, timedelta
from .models import *
from .forms import JobForm, JobApplicationForm, WorkerProfileForm, JobSearchForm, WorkerSearchForm


def home(request):
    """Homepage with search functionality"""
    # Get recent jobs and top-rated workers
    recent_jobs = Job.objects.filter(status='OPEN').order_by('-created_at')[:6]
    top_workers = WorkerProfile.objects.filter(
        is_available=True, num_ratings__gt=0
    ).order_by('-rating')[:8]
    
    # Get skill categories for search
    categories = SkillCategory.objects.filter(is_active=True)
    
    context = {
        'recent_jobs': recent_jobs,
        'top_workers': top_workers,
        'categories': categories,
    }
    return render(request, 'core/index.html', context)


@login_required
def dashboard(request):
    """Main dashboard view - redirects to appropriate dashboard based on user type"""
    if request.user.user_type == 'CLIENT':
        return redirect('core:client_dashboard')
    elif request.user.user_type == 'WORKER':
        return redirect('core:worker_dashboard')
    else:
        messages.error(request, 'Invalid user type')
        return redirect('core:home')


@login_required
def client_dashboard(request):
    """Client dashboard with job management and analytics"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Access denied. Client dashboard only.')
        return redirect('core:home')
    
    # Get client's jobs
    posted_jobs = request.user.jobs_posted.all()
    active_jobs = posted_jobs.filter(status__in=['OPEN', 'ASSIGNED', 'IN_PROGRESS'])
    completed_jobs = posted_jobs.filter(status='COMPLETED')
    draft_jobs = posted_jobs.filter(status='DRAFT')
    
    # Analytics
    total_spent = completed_jobs.aggregate(
        total=Sum('budget_max')
    )['total'] or 0
    
    # Recent activity
    recent_applications = JobApplication.objects.filter(
        job__client=request.user
    ).order_by('-applied_at')[:5]
    
    # Upcoming jobs
    upcoming_jobs = active_jobs.filter(
        scheduled_for__gte=timezone.now()
    ).order_by('scheduled_for')[:5]
    
    # Monthly job statistics
    current_month = timezone.now().month
    monthly_jobs = posted_jobs.filter(
        created_at__month=current_month
    ).count()
    
    context = {
        'posted_jobs': posted_jobs,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'draft_jobs': draft_jobs,
        'total_spent': total_spent,
        'recent_applications': recent_applications,
        'upcoming_jobs': upcoming_jobs,
        'monthly_jobs': monthly_jobs,
        'total_jobs': posted_jobs.count(),
        'pending_applications': JobApplication.objects.filter(
            job__client=request.user, 
            status='PENDING'
        ).count(),
    }
    return render(request, 'core/dashboard/client_dashboard.html', context)


@login_required
def worker_dashboard(request):
    """Worker dashboard with job applications and earnings"""
    if request.user.user_type != 'WORKER':
        messages.error(request, 'Access denied. Worker dashboard only.')
        return redirect('core:home')
    
    try:
        worker_profile = request.user.worker_profile
    except WorkerProfile.DoesNotExist:
        messages.error(request, 'Worker profile not found. Please complete your profile.')
        return redirect('accounts:profile')
    
    # Get worker's applications and jobs
    applications = worker_profile.applications.all()
    accepted_applications = applications.filter(status='ACCEPTED')
    pending_applications = applications.filter(status='PENDING')
    
    # Get assigned jobs
    assigned_jobs = Job.objects.filter(assigned_worker=worker_profile)
    active_jobs = assigned_jobs.filter(status__in=['ASSIGNED', 'IN_PROGRESS'])
    completed_jobs = assigned_jobs.filter(status='COMPLETED')
    
    # Earnings calculation (simplified)
    total_earnings = completed_jobs.aggregate(
        total=Sum('budget_max')
    )['total'] or 0
    
    # Monthly earnings
    current_month = timezone.now().month
    monthly_earnings = completed_jobs.filter(
        completed_at__month=current_month
    ).aggregate(total=Sum('budget_max'))['total'] or 0
    
    # Recent job opportunities
    recent_jobs = Job.objects.filter(
        status='OPEN',
        required_skills__in=worker_profile.skills.all()
    ).exclude(
        applications__worker=worker_profile
    ).distinct().order_by('-created_at')[:5]
    
    # Performance metrics
    avg_rating = worker_profile.rating
    total_jobs_completed = worker_profile.total_jobs_completed
    
    context = {
        'worker_profile': worker_profile,
        'applications': applications,
        'accepted_applications': accepted_applications,
        'pending_applications': pending_applications,
        'active_jobs': active_jobs,
        'completed_jobs': completed_jobs,
        'total_earnings': total_earnings,
        'monthly_earnings': monthly_earnings,
        'recent_jobs': recent_jobs,
        'avg_rating': avg_rating,
        'total_jobs_completed': total_jobs_completed,
        'acceptance_rate': (accepted_applications.count() / applications.count() * 100) if applications.count() > 0 else 0,
    }
    return render(request, 'core/dashboard/worker_dashboard.html', context)


@login_required
def client_jobs(request):
    """Client's job management page"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    jobs = request.user.jobs_posted.all()
    status_filter = request.GET.get('status', '')
    
    if status_filter:
        jobs = jobs.filter(status=status_filter)
    
    paginator = Paginator(jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'jobs': page_obj,
        'status_filter': status_filter,
        'total_jobs': jobs.count(),
    }
    return render(request, 'core/dashboard/client_jobs.html', context)


@login_required
def client_draft_jobs(request):
    """Client's draft jobs management page"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    draft_jobs = request.user.jobs_posted.filter(status='DRAFT').order_by('-created_at')
    
    paginator = Paginator(draft_jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'draft_jobs': page_obj,
        'total_drafts': draft_jobs.count(),
    }
    return render(request, 'core/dashboard/client_draft_jobs.html', context)


@login_required
def delete_draft_job(request, job_id):
    """Client deletes a draft job"""
    if request.user.user_type != 'CLIENT':
        return JsonResponse({'success': False, 'error': 'Access denied'})
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    try:
        job = Job.objects.get(id=job_id, client=request.user, status='DRAFT')
        job.delete()
        return JsonResponse({'success': True})
    except Job.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Job not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def post_job(request):
    """Client posts a new job"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Only clients can post jobs.')
        return redirect('core:home')
    
    if request.method == 'POST':
        form = JobForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.client = request.user
            
            # Determine status based on button clicked
            if 'save_draft' in request.POST:
                job.status = 'DRAFT'
                messages.success(request, 'Job saved as draft successfully!')
            else:
                job.status = 'OPEN'
                messages.success(request, 'Job posted successfully!')
            
            job.save()
            form.save_m2m()  # Save many-to-many relationships
            
            return redirect('core:client_jobs')
    else:
        form = JobForm()
    
    context = {
        'form': form,
    }
    return render(request, 'core/dashboard/post_job.html', context)


@login_required
def edit_job(request, job_id):
    """Client edits an existing job"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    job = get_object_or_404(Job, id=job_id, client=request.user)
    
    if request.method == 'POST':
        form = JobForm(request.POST, instance=job)
        if form.is_valid():
            job = form.save(commit=False)
            
            # Determine status based on button clicked
            if 'save_draft' in request.POST:
                job.status = 'DRAFT'
                messages.success(request, 'Job updated and saved as draft!')
            else:
                job.status = 'OPEN'
                messages.success(request, 'Job updated and published!')
            
            job.save()
            form.save_m2m()
            
            return redirect('core:client_jobs')
    else:
        form = JobForm(instance=job)
        
        # Check if this is a publish action from draft page
        action = request.GET.get('action')
        if action == 'publish' and job.status == 'DRAFT':
            # Pre-fill the form and show publish message
            messages.info(request, 'You can now review and publish your draft job. Make any final changes and click "Publish Job" when ready.')
    
    context = {
        'form': form,
        'job': job,
        'is_publishing_draft': request.GET.get('action') == 'publish' and job.status == 'DRAFT',
    }
    return render(request, 'core/dashboard/post_job.html', context)


@login_required
def worker_profile(request):
    """Worker profile management"""
    if request.user.user_type != 'WORKER':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    try:
        worker_profile = request.user.worker_profile
    except WorkerProfile.DoesNotExist:
        # Create worker profile if it doesn't exist
        worker_profile = WorkerProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = WorkerProfileForm(request.POST, instance=worker_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('core:worker_profile')
    else:
        form = WorkerProfileForm(instance=worker_profile)
    
    context = {
        'form': form,
        'worker_profile': worker_profile,
    }
    return render(request, 'core/dashboard/worker_profile.html', context)


def worker_public_profile(request, worker_id):
    """Public worker profile page"""
    worker_profile = get_object_or_404(WorkerProfile, id=worker_id)
    
    # Get worker's completed jobs
    completed_jobs = Job.objects.filter(
        assigned_worker=worker_profile,
        status='COMPLETED'
    ).order_by('-completed_at')[:5]
    
    # Get recent ratings
    recent_ratings = Rating.objects.filter(
        ratee=worker_profile.user,
        rating_type='CLIENT_TO_WORKER'
    ).order_by('-created_at')[:5]
    
    # Get worker's skills with proficiency
    worker_skills = WorkerSkill.objects.filter(worker=worker_profile).select_related('skill')
    
    # Get worker's availability
    availability = WorkerAvailability.objects.filter(worker=worker_profile)
    
    # Calculate statistics
    total_earnings = completed_jobs.aggregate(total=Sum('budget_max'))['total'] or 0
    avg_rating = worker_profile.rating
    total_jobs = worker_profile.total_jobs_completed
    
    # Check if current user can contact this worker
    can_contact = request.user.is_authenticated and request.user.user_type == 'CLIENT'
    
    context = {
        'worker_profile': worker_profile,
        'completed_jobs': completed_jobs,
        'recent_ratings': recent_ratings,
        'worker_skills': worker_skills,
        'availability': availability,
        'total_earnings': total_earnings,
        'avg_rating': avg_rating,
        'total_jobs': total_jobs,
        'can_contact': can_contact,
    }
    return render(request, 'core/worker_public_profile.html', context)


def browse_jobs(request):
    """Browse and search jobs"""
    form = JobSearchForm(request.GET)
    jobs = Job.objects.filter(status='OPEN')
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        category = form.cleaned_data.get('category')
        location = form.cleaned_data.get('location')
        budget_min = form.cleaned_data.get('budget_min')
        budget_max = form.cleaned_data.get('budget_max')
        
        if query:
            jobs = jobs.filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )
        
        if category:
            jobs = jobs.filter(required_skills__category=category)
        
        if location:
            jobs = jobs.filter(location__icontains=location)
        
        if budget_min:
            jobs = jobs.filter(budget_max__gte=budget_min)
        
        if budget_max:
            jobs = jobs.filter(budget_min__lte=budget_max)
    
    jobs = jobs.distinct().order_by('-created_at')
    
    paginator = Paginator(jobs, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'jobs': page_obj,
        'form': form,
    }
    return render(request, 'core/browse_jobs.html', context)


def browse_workers(request):
    """Browse and search workers"""
    form = WorkerSearchForm(request.GET)
    workers = WorkerProfile.objects.filter(is_available=True)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        skill = form.cleaned_data.get('skill')
        experience_level = form.cleaned_data.get('experience_level')
        max_rate = form.cleaned_data.get('max_rate')
        
        if query:
            workers = workers.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(bio__icontains=query)
            )
        
        if skill:
            workers = workers.filter(skills=skill)
        
        if experience_level:
            workers = workers.filter(experience_level=experience_level)
        
        if max_rate:
            workers = workers.filter(hourly_rate__lte=max_rate)
    
    workers = workers.distinct().order_by('-rating')
    
    paginator = Paginator(workers, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'workers': page_obj,
        'form': form,
    }
    return render(request, 'core/browse_workers.html', context)


@login_required
def worker_applications(request):
    """Worker's job applications page"""
    if request.user.user_type != 'WORKER':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    try:
        worker_profile = request.user.worker_profile
    except WorkerProfile.DoesNotExist:
        messages.error(request, 'Worker profile not found.')
        return redirect('accounts:profile')
    
    applications = worker_profile.applications.all()
    status_filter = request.GET.get('status', '')
    
    if status_filter:
        applications = applications.filter(status=status_filter)
    
    paginator = Paginator(applications, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'applications': page_obj,
        'status_filter': status_filter,
        'total_applications': applications.count(),
    }
    return render(request, 'core/dashboard/worker_applications.html', context)


@login_required
def job_detail(request, job_id):
    """Detailed view of a job with applications"""
    job = get_object_or_404(Job, id=job_id)
    
    # Check if user has permission to view this job
    if request.user.user_type == 'CLIENT' and job.client != request.user:
        messages.error(request, 'Access denied.')
        return redirect('core:client_dashboard')
    
    if request.user.user_type == 'WORKER':
        try:
            worker_profile = request.user.worker_profile
            user_application = job.applications.filter(worker=worker_profile).first()
        except WorkerProfile.DoesNotExist:
            user_application = None
    else:
        user_application = None
    
    context = {
        'job': job,
        'applications': job.applications.all() if request.user.user_type == 'CLIENT' else None,
        'user_application': user_application,
    }
    return render(request, 'core/dashboard/job_detail.html', context)


@login_required
def apply_for_job(request, job_id):
    """Worker applies for a job"""
    if request.user.user_type != 'WORKER':
        messages.error(request, 'Only workers can apply for jobs.')
        return redirect('core:home')
    
    job = get_object_or_404(Job, id=job_id, status='OPEN')
    
    try:
        worker_profile = request.user.worker_profile
    except WorkerProfile.DoesNotExist:
        messages.error(request, 'Please complete your worker profile first.')
        return redirect('accounts:profile')
    
    # Check if already applied
    if job.applications.filter(worker=worker_profile).exists():
        messages.warning(request, 'You have already applied for this job.')
        return redirect('core:job_detail', job_id=job_id)
    
    if request.method == 'POST':
        form = JobApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.job = job
            application.worker = worker_profile
            application.save()
            
            # Create notification for client
            Notification.objects.create(
                user=job.client,
                title=f'New Application for {job.title}',
                message=f'{request.user.get_full_name()} has applied for your job.',
                notification_type='APPLICATION_RECEIVED',
                related_job=job
            )
            
            messages.success(request, 'Application submitted successfully!')
            return redirect('core:job_detail', job_id=job_id)
    else:
        form = JobApplicationForm()
    
    context = {
        'job': job,
        'form': form,
    }
    return render(request, 'core/dashboard/apply_for_job.html', context)


@login_required
def manage_applications(request, job_id):
    """Client manages applications for their job"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    job = get_object_or_404(Job, id=job_id, client=request.user)
    applications = job.applications.all()
    
    context = {
        'job': job,
        'applications': applications,
    }
    return render(request, 'core/dashboard/manage_applications.html', context)


@login_required
def accept_application(request, application_id):
    """Client accepts a job application"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    application = get_object_or_404(JobApplication, id=application_id)
    
    if application.job.client != request.user:
        messages.error(request, 'Access denied.')
        return redirect('core:client_dashboard')
    
    if application.status != 'PENDING':
        messages.error(request, 'Application is not pending.')
        return redirect('core:manage_applications', job_id=application.job.id)
    
    # Accept the application
    application.status = 'ACCEPTED'
    application.responded_at = timezone.now()
    application.save()
    
    # Update job status
    job = application.job
    job.status = 'ASSIGNED'
    job.assigned_worker = application.worker
    job.save()
    
    # Reject other applications
    other_applications = job.applications.exclude(id=application.id)
    for app in other_applications:
        app.status = 'REJECTED'
        app.responded_at = timezone.now()
        app.save()
    
    # Create notifications
    Notification.objects.create(
        user=application.worker.user,
        title=f'Application Accepted - {job.title}',
        message=f'Your application for "{job.title}" has been accepted!',
        notification_type='APPLICATION_ACCEPTED',
        related_job=job
    )
    
    messages.success(request, 'Application accepted successfully!')
    return redirect('core:manage_applications', job_id=job.id)


@login_required
def reject_application(request, application_id):
    """Client rejects a job application"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    
    application = get_object_or_404(JobApplication, id=application_id)
    
    if application.job.client != request.user:
        messages.error(request, 'Access denied.')
        return redirect('core:client_dashboard')
    
    if application.status != 'PENDING':
        messages.error(request, 'Application is not pending.')
        return redirect('core:manage_applications', job_id=application.job.id)
    
    # Reject the application
    application.status = 'REJECTED'
    application.responded_at = timezone.now()
    application.save()
    
    # Create notification
    Notification.objects.create(
        user=application.worker.user,
        title=f'Application Update - {application.job.title}',
        message=f'Your application for "{application.job.title}" was not selected.',
        notification_type='APPLICATION_REJECTED',
        related_job=application.job
    )
    
    messages.success(request, 'Application rejected.')
    return redirect('core:manage_applications', job_id=application.job.id)


@require_http_methods(["GET"])
def search_jobs(request):
    """AJAX search for jobs"""
    query = request.GET.get('q', '')
    location = request.GET.get('location', '')
    category = request.GET.get('category', '')
    
    jobs = Job.objects.filter(status='OPEN')
    
    if query:
        jobs = jobs.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )
    
    if category:
        jobs = jobs.filter(required_skills__category__id=category)
    
    # Location-based search would require PostGIS setup
    jobs = jobs.distinct().order_by('-created_at')[:10]
    
    context = {'jobs': jobs}
    return render(request, 'core/partials/job_cards.html', context)


@require_http_methods(["GET"])
def search_workers(request):
    """AJAX search for workers"""
    query = request.GET.get('q', '')
    skill = request.GET.get('skill', '')
    
    workers = WorkerProfile.objects.filter(is_available=True)
    
    if query:
        workers = workers.filter(
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query) |
            Q(bio__icontains=query)
        )
    
    if skill:
        workers = workers.filter(skills__id=skill)
    
    workers = workers.distinct().order_by('-rating')[:10]
    
    context = {'workers': workers}
    return render(request, 'core/partials/worker_cards.html', context)


@login_required
def notifications(request):
    """Get user notifications"""
    notifications = request.user.notifications.order_by('-created_at')[:10]
    context = {'notifications': notifications}
    return render(request, 'core/partials/notifications.html', context)