# core/ai_services.py - Fixes needed
import math
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Q, Avg, Count, Sum
from .models import (
    Job, WorkerProfile, JobApplication, Rating, AIMatchingScore, 
    WorkerSkill, WorkerAvailability, Skill, User, SkillCategory
)
import logging

logger = logging.getLogger(__name__)


class AIMatchingEngine:
    """
    Advanced AI matching engine for job-worker compatibility
    """
    
    # Scoring weights for different factors
    WEIGHTS = {
        'skill_match': 0.30,        # Skills compatibility
        'experience_match': 0.20,   # Experience level match
        'rating_score': 0.15,       # Worker rating
        'availability_match': 0.10, # Time availability
        'location_proximity': 0.10, # Distance factor
        'budget_compatibility': 0.10, # Budget alignment
        'historical_performance': 0.05  # Past job performance
    }
    
    @classmethod
    def calculate_compatibility_score(cls, job, worker_profile):
        """
        Calculate comprehensive compatibility score between job and worker
        Returns: float (0.0 to 1.0)
        """
        try:
            factors = {}
            
            # 1. Skill Match Score
            factors['skill_match'] = cls._calculate_skill_match(job, worker_profile)
            
            # 2. Experience Match Score
            factors['experience_match'] = cls._calculate_experience_match(job, worker_profile)
            
            # 3. Rating Score
            factors['rating_score'] = cls._calculate_rating_score(worker_profile)
            
            # 4. Availability Match
            factors['availability_match'] = cls._calculate_availability_match(job, worker_profile)
            
            # 5. Location Proximity (simplified without PostGIS)
            factors['location_proximity'] = cls._calculate_location_proximity(job, worker_profile)
            
            # 6. Budget Compatibility
            factors['budget_compatibility'] = cls._calculate_budget_compatibility(job, worker_profile)
            
            # 7. Historical Performance
            factors['historical_performance'] = cls._calculate_historical_performance(worker_profile)
            
            # Calculate weighted final score
            final_score = sum(
                factors[factor] * cls.WEIGHTS[factor] 
                for factor in factors
            )
            
            return min(1.0, max(0.0, final_score)), factors
            
        except Exception as e:
            logger.error(f"Error calculating compatibility score: {e}")
            return 0.0, {}
    
    @staticmethod
    def _calculate_skill_match(job, worker_profile):
        """Calculate skill compatibility score"""
        required_skills = set(job.required_skills.all())
        if not required_skills:
            return 0.8  # Neutral score if no specific skills required
        
        worker_skills = set(worker_profile.skills.all())
        if not worker_skills:
            return 0.0
        
        # Basic skill overlap
        skill_overlap = len(required_skills.intersection(worker_skills))
        basic_score = skill_overlap / len(required_skills)
        
        # Enhanced scoring based on proficiency levels
        proficiency_bonus = 0.0
        for skill in required_skills.intersection(worker_skills):
            try:
                worker_skill = WorkerSkill.objects.get(worker=worker_profile, skill=skill)
                proficiency_multiplier = {
                    'BASIC': 0.6,
                    'INTERMEDIATE': 0.8,
                    'ADVANCED': 0.95,
                    'EXPERT': 1.0
                }.get(worker_skill.proficiency, 0.6)
                proficiency_bonus += proficiency_multiplier / len(required_skills)
            except WorkerSkill.DoesNotExist:
                proficiency_bonus += 0.6 / len(required_skills)
        
        return min(1.0, basic_score * 0.7 + proficiency_bonus * 0.3)
    
    @staticmethod
    def _calculate_experience_match(job, worker_profile):
        """Calculate experience level compatibility"""
        experience_levels = ['BEGINNER', 'INTERMEDIATE', 'EXPERIENCED', 'EXPERT']
        
        # Handle case where experience_level might be None
        if not worker_profile.experience_level:
            return 0.5
            
        try:
            worker_level_index = experience_levels.index(worker_profile.experience_level)
        except ValueError:
            worker_level_index = 0  # Default to BEGINNER if not found
        
        # Job complexity estimation based on budget and skills required
        job_complexity = 0
        if job.budget_max:
            if job.budget_max > 500:
                job_complexity += 1
            if job.budget_max > 1000:
                job_complexity += 1
        
        if job.required_skills.count() > 3:
            job_complexity += 1
        
        # Match experience to job complexity
        optimal_level = min(job_complexity, len(experience_levels) - 1)
        level_difference = abs(worker_level_index - optimal_level)
        
        return max(0.0, 1.0 - (level_difference * 0.2))
    
    @staticmethod
    def _calculate_rating_score(worker_profile):
        """Convert worker rating to normalized score"""
        if worker_profile.num_ratings == 0:
            return 0.5  # Neutral score for new workers
        
        # Normalize 5-star rating to 0-1 scale with reliability factor
        base_score = worker_profile.rating / 5.0
        
        # Reliability factor based on number of ratings
        reliability_factor = min(1.0, worker_profile.num_ratings / 10.0)
        
        return base_score * (0.7 + 0.3 * reliability_factor)
    
    @staticmethod
    def _calculate_availability_match(job, worker_profile):
        """Calculate availability compatibility"""
        if not job.scheduled_for:
            return 0.8  # Neutral if no specific scheduling
        
        try:
            job_day = job.scheduled_for.weekday()
            job_time = job.scheduled_for.time()
            
            availability = WorkerAvailability.objects.filter(
                worker=worker_profile,
                day_of_week=job_day,
                is_available=True,
                start_time__lte=job_time,
                end_time__gte=job_time
            )
            
            return 1.0 if availability.exists() else 0.3
            
        except Exception:
            return 0.5
    
    @staticmethod
    def _calculate_location_proximity(job, worker_profile):
        """Calculate location compatibility (simplified)"""
        try:
            job_location = job.location.lower() if job.location else ""
            worker_location = getattr(worker_profile.user, 'location', '').lower()
            
            if not job_location or not worker_location:
                return 0.7  # Neutral score if location data missing
            
            # Simple string matching for city/state
            if job_location in worker_location or worker_location in job_location:
                return 1.0
            
            # Extract common location keywords
            job_keywords = set(job_location.split())
            worker_keywords = set(worker_location.split())
            common_keywords = job_keywords.intersection(worker_keywords)
            
            if common_keywords:
                return 0.8
            
            return 0.4  # Different locations
            
        except Exception:
            return 0.5
    
    @staticmethod
    def _calculate_budget_compatibility(job, worker_profile):
        """Calculate budget alignment score"""
        if not worker_profile.hourly_rate or not job.estimated_duration:
            return 0.7  # Neutral if insufficient data
        
        estimated_cost = float(worker_profile.hourly_rate) * job.estimated_duration
        
        if job.budget_max:
            if estimated_cost <= job.budget_max:
                # Perfect if within budget
                if job.budget_min and estimated_cost >= job.budget_min:
                    return 1.0
                else:
                    return 0.9
            else:
                # Penalty for exceeding budget
                excess_ratio = (estimated_cost - job.budget_max) / job.budget_max
                return max(0.0, 1.0 - excess_ratio)
        
        return 0.7
    
    @staticmethod
    def _calculate_historical_performance(worker_profile):
        """Calculate historical performance score"""
        completed_jobs = worker_profile.total_jobs_completed
        
        if completed_jobs == 0:
            return 0.5  # Neutral for new workers
        
        # Performance factors
        completion_score = min(1.0, completed_jobs / 20.0)  # Normalize to 20 jobs
        
        # Check recent job completion rate
        recent_jobs = Job.objects.filter(
            assigned_worker=worker_profile,
            created_at__gte=timezone.now() - timedelta(days=90)
        )
        
        if recent_jobs.exists():
            completed_recent = recent_jobs.filter(status='COMPLETED').count()
            completion_rate = completed_recent / recent_jobs.count()
            return (completion_score * 0.6) + (completion_rate * 0.4)
        
        return completion_score


# ... rest of the file remains the same ...