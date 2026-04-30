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
from .ai_services import AIMatchingEngine
from django.contrib.auth import get_user_model


def user_has_learning_access(user):
    """
    Hybrid access for workers/learners: free if at least one skill is listed,
    else an active subscription. Clients (job/request posters) always have access.
    """
    if not user.is_authenticated:
        return False
    ut = getattr(user, 'user_type', None)
    # Clients post skill requests — they are not required to list a worker skill
    if ut == 'CLIENT':
        return True
    if ut == 'ADMIN' or getattr(user, 'is_staff', False):
        return True
    # Workers: need a listed skill or learner subscription
    return bool(getattr(user, 'has_listed_skill', False) or getattr(user, 'subscription_active', False))


def enforce_learning_access(request):
    """Guard views that require platform participation access."""
    if user_has_learning_access(request.user):
        return None
    messages.warning(
        request,
        'List at least one skill for free access, or activate subscription to continue.'
    )
    return redirect('core:home')


@login_required
def admin_dashboard(request):
    """Lightweight admin dashboard to approve jobs and workers"""
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'ADMIN'):
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    # Filters
    job_query = request.GET.get('jq', '')
    worker_query = request.GET.get('wq', '')
    user_query = request.GET.get('uq', '')
    job_status = request.GET.get('status', '')
    job_approval = request.GET.get('japproved', '')
    worker_approval = request.GET.get('wapproved', '')
    user_type = request.GET.get('utype', '')
    user_active = request.GET.get('uactive', '')

    jobs_qs = Job.objects.all().order_by('-created_at')
    if job_query:
        jobs_qs = jobs_qs.filter(Q(title__icontains=job_query) | Q(description__icontains=job_query) | Q(client__username__icontains=job_query))
    if job_status:
        jobs_qs = jobs_qs.filter(status=job_status)
    if job_approval in ['approved', 'pending']:
        jobs_qs = jobs_qs.filter(is_approved=(job_approval == 'approved'))

    workers_qs = WorkerProfile.objects.select_related('user').all().order_by('-created_at')
    if worker_query:
        workers_qs = workers_qs.filter(Q(user__first_name__icontains=worker_query) | Q(user__last_name__icontains=worker_query) | Q(user__username__icontains=worker_query))
    if worker_approval in ['approved', 'pending']:
        workers_qs = workers_qs.filter(is_approved=(worker_approval == 'approved'))

    # Simple pagination
    jobs_page = Paginator(jobs_qs, 10).get_page(request.GET.get('jpage'))
    workers_page = Paginator(workers_qs, 10).get_page(request.GET.get('wpage'))
    # Users
    UserModel = get_user_model()
    users_qs = UserModel.objects.all().order_by('-date_joined')
    if user_query:
        users_qs = users_qs.filter(
            Q(username__icontains=user_query) |
            Q(email__icontains=user_query) |
            Q(first_name__icontains=user_query) |
            Q(last_name__icontains=user_query)
        )
    if user_type:
        users_qs = users_qs.filter(user_type=user_type)
    if user_active in ['active', 'inactive']:
        users_qs = users_qs.filter(is_active=(user_active == 'active'))
    users_page = Paginator(users_qs, 10).get_page(request.GET.get('upage'))

    # KPIs
    total_jobs = Job.objects.count()
    pending_jobs_count = Job.objects.filter(is_approved=False).count()
    total_workers = WorkerProfile.objects.count()
    pending_workers_count = WorkerProfile.objects.filter(is_approved=False).count()
    completed_jobs = Job.objects.filter(status='COMPLETED').count()
    total_users = UserModel.objects.count()
    active_users = UserModel.objects.filter(is_active=True).count()

    context = {
        'jobs': jobs_page,
        'workers': workers_page,
        'users': users_page,
        'kpi': {
            'total_jobs': total_jobs,
            'pending_jobs': pending_jobs_count,
            'total_workers': total_workers,
            'pending_workers': pending_workers_count,
            'completed_jobs': completed_jobs,
            'total_users': total_users,
            'active_users': active_users,
        },
        'filters': {
            'job_query': job_query,
            'worker_query': worker_query,
            'user_query': user_query,
            'job_status': job_status,
            'job_approval': job_approval,
            'worker_approval': worker_approval,
            'user_type': user_type,
            'user_active': user_active,
        }
    }
    return render(request, 'core/dashboard/admin_dashboard.html', context)


@login_required
def approve_job(request, job_id):
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'ADMIN'):
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    job = get_object_or_404(Job, id=job_id)
    job.is_approved = True
    job.save()
    messages.success(request, 'Job approved!')
    return redirect('core:admin_dashboard')


@login_required
def approve_worker(request, worker_id):
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'ADMIN'):
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    worker = get_object_or_404(WorkerProfile, id=worker_id)
    worker.is_approved = True
    worker.save()
    messages.success(request, 'Worker approved!')
    return redirect('core:admin_dashboard')


@login_required
def admin_job_action(request, job_id):
    if request.method != 'POST':
        return redirect('core:admin_dashboard')
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'ADMIN'):
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    job = get_object_or_404(Job, id=job_id)
    action = request.POST.get('action')
    try:
        if action == 'save':
            status = request.POST.get('status')
            priority = request.POST.get('priority')
            is_approved = request.POST.get('is_approved') == 'on'
            title = request.POST.get('title')
            budget_min = request.POST.get('budget_min')
            budget_max = request.POST.get('budget_max')
            if status in dict(Job.JOB_STATUS):
                job.status = status
            if priority in dict(Job.PRIORITY_LEVELS):
                job.priority = priority
            job.is_approved = is_approved
            if title:
                job.title = title
            if budget_min not in [None, '']:
                try:
                    job.budget_min = float(budget_min)
                except ValueError:
                    pass
            if budget_max not in [None, '']:
                try:
                    job.budget_max = float(budget_max)
                except ValueError:
                    pass
            job.save()
            messages.success(request, 'Job updated.')
        elif action == 'delete':
            job.delete()
            messages.success(request, 'Job deleted.')
        elif action == 'approve':
            job.is_approved = True
            job.save()
            messages.success(request, 'Job approved!')
        else:
            messages.error(request, 'Unknown action.')
    except Exception as e:
        messages.error(request, f'Error: {e}')
    return redirect('core:admin_dashboard')


@login_required
def admin_worker_action(request, worker_id):
    if request.method != 'POST':
        return redirect('core:admin_dashboard')
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'ADMIN'):
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    worker = get_object_or_404(WorkerProfile, id=worker_id)
    action = request.POST.get('action')
    try:
        if action == 'save':
            is_available = request.POST.get('is_available') == 'on'
            background_verified = request.POST.get('background_verified') == 'on'
            is_approved = request.POST.get('is_approved') == 'on'
            experience_level = request.POST.get('experience_level')
            worker.is_available = is_available
            worker.background_verified = background_verified
            worker.is_approved = is_approved
            if experience_level in dict(WorkerProfile.EXPERIENCE_LEVELS):
                worker.experience_level = experience_level
            worker.save()
            messages.success(request, 'Worker updated.')
        elif action == 'delete':
            user = worker.user
            worker.delete()
            messages.success(request, 'Worker profile deleted.')
        elif action == 'approve':
            worker.is_approved = True
            worker.save()
            messages.success(request, 'Worker approved!')
        else:
            messages.error(request, 'Unknown action.')
    except Exception as e:
        messages.error(request, f'Error: {e}')
    return redirect('core:admin_dashboard')


@login_required
def admin_user_action(request, user_id):
    if request.method != 'POST':
        return redirect('core:admin_dashboard')
    if not (request.user.is_staff or getattr(request.user, 'user_type', '') == 'ADMIN'):
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    UserModel = get_user_model()
    user = get_object_or_404(UserModel, id=user_id)
    action = request.POST.get('action')
    try:
        if action == 'save':
            first_name = request.POST.get('first_name')
            last_name = request.POST.get('last_name')
            email = request.POST.get('email')
            user_type = request.POST.get('user_type')
            is_active = request.POST.get('is_active') == 'on'
            is_staff = request.POST.get('is_staff') == 'on'
            is_verified = request.POST.get('is_verified') == 'on'
            has_listed_skill = request.POST.get('has_listed_skill') == 'on'
            subscription_active = request.POST.get('subscription_active') == 'on'
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if email is not None:
                user.email = email
            # If custom user has USER_TYPES
            if hasattr(user, 'USER_TYPES') and user_type in dict(user.USER_TYPES):
                user.user_type = user_type
            user.is_active = is_active
            user.is_staff = is_staff
            if hasattr(user, 'is_verified'):
                user.is_verified = is_verified
            if hasattr(user, 'has_listed_skill'):
                user.has_listed_skill = has_listed_skill
            if hasattr(user, 'subscription_active'):
                user.subscription_active = subscription_active
            user.save()
            messages.success(request, 'User updated.')
        elif action == 'delete':
            if user == request.user:
                messages.error(request, 'You cannot delete the currently logged-in user.')
            else:
                user.delete()
                messages.success(request, 'User deleted.')
        else:
            messages.error(request, 'Unknown action.')
    except Exception as e:
        messages.error(request, f'Error: {e}')
    return redirect('core:admin_dashboard')


def home(request):
    """Homepage with search functionality and personalized recommendations"""
    # Get recent jobs and top-rated workers
    recent_jobs = Job.objects.filter(status='OPEN', is_approved=True).order_by('-created_at')[:6]
    top_workers = WorkerProfile.objects.filter(
        is_available=True, is_approved=True, num_ratings__gt=0
    ).order_by('-rating')[:8]
    
    # Get skill categories for search
    categories = SkillCategory.objects.filter(is_active=True)
    
    # Initialize recommendation variables
    recommended_workers = None
    recommended_jobs = None
    
    # If user is logged in, show personalized recommendations
    if request.user.is_authenticated:
        try:
            if request.user.user_type == 'CLIENT':
                recommended_workers = get_recommended_workers_for_client(request.user)
            elif request.user.user_type == 'WORKER':
                recommended_jobs = get_recommended_jobs_for_worker(request.user)
        except Exception as e:
            # Log error and continue without recommendations
            print(f"Error getting recommendations: {e}")
            recommended_workers = None
            recommended_jobs = None
    
    context = {
        'recent_jobs': recent_jobs,
        'top_workers': top_workers,
        'categories': categories,
        'recommended_workers': recommended_workers,
        'recommended_jobs': recommended_jobs,
    }
    return render(request, 'core/index.html', context)


def get_recommended_workers_for_client(client, limit=6):
    """Get recommended workers with location-aware scoring and skills."""
    try:
        # Consider only approved jobs from client history
        recent_jobs = client.jobs_posted.filter(status__in=['OPEN', 'ASSIGNED', 'IN_PROGRESS', 'COMPLETED'], is_approved=True)
        
        # No job history: proximity + rating
        if not recent_jobs.exists():
            client_loc = (client.location or '').lower()
            candidates = WorkerProfile.objects.filter(is_available=True, is_approved=True)

            def loc_score(worker):
                wloc = (worker.user.location or '').lower()
                if client_loc and wloc:
                    if client_loc in wloc or wloc in client_loc:
                        return 1.0
                    s1 = set(client_loc.split())
                    s2 = set(wloc.split())
                    return 0.7 if s1 & s2 else 0.3
                return 0.5

            ranked = sorted(candidates, key=lambda w: (loc_score(w), w.rating, w.is_available), reverse=True)
            return ranked[:limit]

        # Use latest job as anchor for AI scoring
        latest_job = recent_jobs.order_by('-created_at').first()
        candidates = WorkerProfile.objects.filter(is_available=True, is_approved=True).distinct()
        scored = []
        for w in candidates:
            score, _ = AIMatchingEngine.calculate_compatibility_score(latest_job, w)
            scored.append((score, w))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [w for s, w in scored[:limit]]

    except Exception:
        try:
            return list(WorkerProfile.objects.filter(is_available=True, is_approved=True, num_ratings__gt=0).order_by('-rating')[:limit])
        except Exception:
            return []


def get_recommended_jobs_for_worker(worker_user, limit=6):
    """Get recommended jobs with skills and location-aware scoring."""
    try:
        worker_profile = getattr(worker_user, 'worker_profile', None)
        if not worker_profile:
            return list(Job.objects.filter(status='OPEN', is_approved=True).order_by('-created_at')[:limit])
        
        worker_skills = worker_profile.skills.all()
        candidate_jobs = Job.objects.filter(status='OPEN', is_approved=True)
        if worker_skills.exists():
            candidate_jobs = candidate_jobs.filter(Q(required_skills__in=worker_skills) | Q(required_skills=None)).distinct()

        scored = []
        for j in candidate_jobs[:200]:
            score, _ = AIMatchingEngine.calculate_compatibility_score(j, worker_profile)
            wloc = (worker_user.location or '').lower()
            jloc = (j.location or '').lower()
            if wloc and jloc and (wloc in jloc or jloc in wloc):
                score = min(1.0, score + 0.1)
            scored.append((score, j))
        scored.sort(key=lambda x: (x[0], x[1].created_at), reverse=True)
        return [j for s, j in scored[:limit]]

    except Exception:
        try:
            return list(Job.objects.filter(status='OPEN', is_approved=True).order_by('-created_at')[:limit])
        except Exception:
            return []


@login_required
def client_recommendations(request):
    """Client's personalized worker recommendations page"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
    # Get recommended workers
    recommended_workers = get_recommended_workers_for_client(request.user, limit=20)
    
    # Get search filters
    skill_filter = request.GET.get('skill', '')
    experience_filter = request.GET.get('experience', '')
    rating_filter = request.GET.get('rating', '')
    
    # Apply filters
    if skill_filter:
        recommended_workers = [w for w in recommended_workers if 
                             any(skill_filter.lower() in skill.name.lower() 
                                  for skill in w.skills.all())]
    
    if experience_filter:
        recommended_workers = [w for w in recommended_workers if 
                             w.experience_level == experience_filter]
    
    if rating_filter:
        min_rating = float(rating_filter)
        recommended_workers = [w for w in recommended_workers if w.rating >= min_rating]
    
    # Pagination
    paginator = Paginator(recommended_workers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all skills and experience levels for filters
    all_skills = Skill.objects.filter(is_active=True)
    experience_levels = WorkerProfile.EXPERIENCE_LEVELS
    
    context = {
        'recommended_workers': page_obj,
        'all_skills': all_skills,
        'experience_levels': experience_levels,
        'skill_filter': skill_filter,
        'experience_filter': experience_filter,
        'rating_filter': rating_filter,
    }
    return render(request, 'core/dashboard/client_recommendations.html', context)


@login_required
def worker_recommendations(request):
    """Worker's personalized job recommendations page"""
    if request.user.user_type != 'WORKER':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
    # Get recommended jobs
    recommended_jobs = get_recommended_jobs_for_worker(request.user, limit=20)
    
    # Get search filters
    skill_filter = request.GET.get('skill', '')
    priority_filter = request.GET.get('priority', '')
    budget_filter = request.GET.get('budget', '')
    
    # Apply filters
    if skill_filter:
        recommended_jobs = [j for j in recommended_jobs if 
                           any(skill_filter.lower() in skill.name.lower() 
                                for skill in j.required_skills.all())]
    
    if priority_filter:
        recommended_jobs = [j for j in recommended_jobs if j.priority == priority_filter]
    
    if budget_filter:
        max_budget = float(budget_filter)
        recommended_jobs = [j for j in recommended_jobs if 
                           (j.budget_max and j.budget_max <= max_budget) or 
                           (j.budget_min and j.budget_min <= max_budget)]
    
    # Pagination
    paginator = Paginator(recommended_jobs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get all skills and priority levels for filters
    all_skills = Skill.objects.filter(is_active=True)
    priority_levels = Job.PRIORITY_LEVELS
    
    context = {
        'recommended_jobs': page_obj,
        'all_skills': all_skills,
        'priority_levels': priority_levels,
        'skill_filter': skill_filter,
        'priority_filter': priority_filter,
        'budget_filter': budget_filter,
    }
    return render(request, 'core/dashboard/worker_recommendations.html', context)


@login_required
def ai_recommendations(request):
    """Unified AI recommendations page showing jobs (for workers) and workers (for clients)."""
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    jobs = []
    workers = []
    if request.user.user_type == 'CLIENT':
        workers = get_recommended_workers_for_client(request.user, limit=12)
    elif request.user.user_type == 'WORKER':
        jobs = get_recommended_jobs_for_worker(request.user, limit=12)
    else:
        # Admins see both top approved snapshots
        workers = list(WorkerProfile.objects.filter(is_available=True, is_approved=True).order_by('-rating')[:12])
        jobs = list(Job.objects.filter(status='OPEN', is_approved=True).order_by('-created_at')[:12])

    context = {
        'recommended_jobs': jobs,
        'recommended_workers': workers,
    }
    return render(request, 'core/dashboard/ai_recommendations.html', context)


@login_required
def dashboard(request):
    """Main dashboard view - redirects to appropriate dashboard based on user type"""
    if request.user.user_type == 'CLIENT':
        return redirect('core:client_dashboard')
    elif request.user.user_type == 'WORKER':
        return redirect('core:worker_dashboard')
    elif request.user.user_type == 'ADMIN' or request.user.is_staff:
        return redirect('core:admin_dashboard')
    else:
        messages.error(request, 'Invalid user type')
        return redirect('core:home')


@login_required
def client_dashboard(request):
    """Client dashboard with job management and analytics"""
    if request.user.user_type != 'CLIENT':
        messages.error(request, 'Access denied. Client dashboard only.')
        return redirect('core:home')
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
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
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
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
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
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
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
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
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
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
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
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
    """Skills profile management (what you can teach + what you want to learn)."""
    
    try:
        worker_profile = request.user.worker_profile
    except WorkerProfile.DoesNotExist:
        # Create worker profile if it doesn't exist
        worker_profile = WorkerProfile.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = WorkerProfileForm(request.POST, instance=worker_profile)
        if form.is_valid():
            saved_profile = form.save()
            request.user.has_listed_skill = saved_profile.skills.exists()
            request.user.save(update_fields=['has_listed_skill'])
            messages.success(request, 'Skills updated successfully!')
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
        status='COMPLETED', is_approved=True
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
    can_contact = request.user.is_authenticated
    
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


@login_required
@require_http_methods(["POST"])
def request_skill_partner(request, worker_id):
    """Send a skill-partner request (creates a message + notification)."""
    worker_profile = get_object_or_404(WorkerProfile, id=worker_id)
    if worker_profile.user_id == request.user.id:
        messages.error(request, "You can't request yourself.")
        return redirect('core:browse_workers')

    note = (request.POST.get('message') or '').strip()
    if not note:
        note = "Hi, I'd like us to connect as skill partners."

    Message.objects.create(
        sender=request.user,
        receiver=worker_profile.user,
        content=note,
    )
    Notification.objects.create(
        user=worker_profile.user,
        title="New skill partner request",
        message=f"{request.user.get_full_name() or request.user.username} sent you a request to connect as skill partners.",
        notification_type="SYSTEM",
    )
    messages.success(request, "Request sent. The student will see it in notifications/messages.")
    return redirect('core:worker_public_profile', worker_id=worker_profile.id)


def browse_jobs(request):
    """Browse and search jobs"""
    if request.user.is_authenticated:
        access_redirect = enforce_learning_access(request)
        if access_redirect:
            return access_redirect
    form = JobSearchForm(request.GET)
    jobs = Job.objects.filter(status='OPEN', is_approved=True)
    
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
    if request.user.is_authenticated:
        access_redirect = enforce_learning_access(request)
        if access_redirect:
            return access_redirect
    form = WorkerSearchForm(request.GET)
    # Show students who have listed at least one skill
    workers = WorkerProfile.objects.select_related('user').filter(user__has_listed_skill=True)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        skill = form.cleaned_data.get('skill')
        experience_level = form.cleaned_data.get('experience_level')
        max_rate = form.cleaned_data.get('max_rate')
        
        if query:
            workers = workers.filter(
                Q(user__first_name__icontains=query) |
                Q(user__last_name__icontains=query) |
                Q(user__username__icontains=query) |
                Q(user__matriculation_number__icontains=query) |
                Q(bio__icontains=query)
            )
            # If query looks like a year (e.g. 2026) also match graduation year
            try:
                q_year = int(query)
                workers = workers | WorkerProfile.objects.select_related('user').filter(
                    user__has_listed_skill=True,
                    user__expected_graduation_year=q_year,
                )
            except (TypeError, ValueError):
                pass
        
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
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
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
def rate_worker(request, job_id):
    """Client or admin rates a worker for a completed job"""
    job = get_object_or_404(Job, id=job_id)
    if request.user.user_type not in ['CLIENT', 'ADMIN'] and not request.user.is_staff:
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    if job.status != 'COMPLETED' or not job.assigned_worker:
        messages.error(request, 'You can only rate completed jobs.')
        return redirect('core:job_detail', job_id=job_id)
    # Only the job client or admin/staff can rate
    if request.user.user_type == 'CLIENT' and job.client != request.user:
        messages.error(request, 'Access denied.')
        return redirect('core:home')

    if request.method == 'POST':
        try:
            stars = int(request.POST.get('stars', '0'))
            comment = request.POST.get('comment', '')
            if stars < 1 or stars > 5:
                raise ValueError('Stars must be 1..5')
            # Create or update rating (client -> worker)
            rating, created = Rating.objects.update_or_create(
                job=job,
                rater=request.user,
                ratee=job.assigned_worker.user,
                rating_type='CLIENT_TO_WORKER',
                defaults={'stars': stars, 'comment': comment}
            )
            # Update worker aggregate
            worker = job.assigned_worker
            # Recompute average rating efficiently
            agg = Rating.objects.filter(ratee=worker.user, rating_type='CLIENT_TO_WORKER').aggregate(
                avg=Avg('stars'), cnt=Count('id')
            )
            worker.rating = float(agg['avg'] or 0.0)
            worker.num_ratings = int(agg['cnt'] or 0)
            worker.save()
            messages.success(request, 'Rating submitted successfully!')
        except Exception as e:
            messages.error(request, f'Error submitting rating: {e}')
    return redirect('core:job_detail', job_id=job_id)


@login_required
def rate_client(request, job_id):
    """Worker rates a client for a completed job they were assigned to"""
    job = get_object_or_404(Job, id=job_id)
    if request.user.user_type != 'WORKER':
        messages.error(request, 'Access denied.')
        return redirect('core:home')
    if job.status != 'COMPLETED' or not job.assigned_worker:
        messages.error(request, 'You can only rate completed jobs.')
        return redirect('core:job_detail', job_id=job_id)
    try:
        worker_profile = request.user.worker_profile
    except WorkerProfile.DoesNotExist:
        messages.error(request, 'Worker profile not found.')
        return redirect('core:home')
    if job.assigned_worker != worker_profile:
        messages.error(request, 'You can only rate jobs assigned to you.')
        return redirect('core:home')

    if request.method == 'POST':
        try:
            stars = int(request.POST.get('stars', '0'))
            comment = request.POST.get('comment', '')
            if stars < 1 or stars > 5:
                raise ValueError('Stars must be 1..5')
            rating, created = Rating.objects.update_or_create(
                job=job,
                rater=request.user,
                ratee=job.client,
                rating_type='WORKER_TO_CLIENT',
                defaults={'stars': stars, 'comment': comment}
            )
            messages.success(request, 'Client rating submitted!')
        except Exception as e:
            messages.error(request, f'Error submitting rating: {e}')
    return redirect('core:job_detail', job_id=job_id)


@login_required
def apply_for_job(request, job_id):
    """Worker applies for a job"""
    if request.user.user_type != 'WORKER':
        messages.error(request, 'Only workers can apply for jobs.')
        return redirect('core:home')
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
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
    access_redirect = enforce_learning_access(request)
    if access_redirect:
        return access_redirect
    
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
    
    jobs = Job.objects.filter(status='OPEN', is_approved=True)
    
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
    
    workers = WorkerProfile.objects.filter(is_available=True, is_approved=True)
    
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