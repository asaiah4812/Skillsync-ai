from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    
    # Dashboard
    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/client/', views.client_dashboard, name='client_dashboard'),
    path('dashboard/worker/', views.worker_dashboard, name='worker_dashboard'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    
    # Recommendations
    path('dashboard/client/recommendations/', views.client_recommendations, name='client_recommendations'),
    path('dashboard/worker/recommendations/', views.worker_recommendations, name='worker_recommendations'),
    path('ai/recommendations/', views.ai_recommendations, name='ai_recommendations'),
    
    # Job management
    path('dashboard/client/jobs/', views.client_jobs, name='client_jobs'),
    path('dashboard/client/jobs/drafts/', views.client_draft_jobs, name='client_draft_jobs'),
    path('dashboard/client/jobs/<uuid:job_id>/delete/', views.delete_draft_job, name='delete_draft_job'),
    path('dashboard/client/jobs/post/', views.post_job, name='post_job'),
    path('dashboard/client/jobs/<uuid:job_id>/edit/', views.edit_job, name='edit_job'),
    path('dashboard/admin/approve/job/<uuid:job_id>/', views.approve_job, name='approve_job'),
    path('dashboard/admin/approve/worker/<int:worker_id>/', views.approve_worker, name='approve_worker'),
    path('dashboard/admin/job/<uuid:job_id>/action/', views.admin_job_action, name='admin_job_action'),
    path('dashboard/admin/worker/<int:worker_id>/action/', views.admin_worker_action, name='admin_worker_action'),
    path('dashboard/admin/user/<uuid:user_id>/action/', views.admin_user_action, name='admin_user_action'),
    path('dashboard/worker/applications/', views.worker_applications, name='worker_applications'),
    path('dashboard/worker/profile/', views.worker_profile, name='worker_profile'),
    
    # Job details and applications
    path('job/<uuid:job_id>/', views.job_detail, name='job_detail'),
    path('job/<uuid:job_id>/apply/', views.apply_for_job, name='apply_for_job'),
    path('job/<uuid:job_id>/applications/', views.manage_applications, name='manage_applications'),
    path('application/<int:application_id>/accept/', views.accept_application, name='accept_application'),
    path('application/<int:application_id>/reject/', views.reject_application, name='reject_application'),
    path('job/<uuid:job_id>/rate/worker/', views.rate_worker, name='rate_worker'),
    path('job/<uuid:job_id>/rate/client/', views.rate_client, name='rate_client'),
    
    # Browse and search
    path('jobs/', views.browse_jobs, name='browse_jobs'),
    path('workers/', views.browse_workers, name='browse_workers'),
    path('worker/<int:worker_id>/', views.worker_public_profile, name='worker_public_profile'),
    path('worker/<int:worker_id>/request/', views.request_skill_partner, name='request_skill_partner'),
    
    # Search functionality
    path('search/jobs/', views.search_jobs, name='search_jobs'),
    path('search/workers/', views.search_workers, name='search_workers'),
    
    # Notifications
    path('notifications/', views.notifications, name='notifications'),
]
