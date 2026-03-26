from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from core.models import SkillCategory, Skill, WorkerProfile, WorkerSkill, Job, JobApplication, Rating


class Command(BaseCommand):
    help = "Seed demo data: categories, skills, users, workers, jobs, applications, ratings"

    def handle(self, *args, **options):
        User = get_user_model()

        # Categories & Skills
        categories = [
            ("Home Services", ["Plumbing", "Electrical", "Carpentry", "Cleaning"]),
            ("Tech & IT", ["Web Development", "Mobile Apps", "Data Analysis", "DevOps"]),
            ("Design & Creative", ["Graphic Design", "UI/UX", "Video Editing", "Content Writing"]),
        ]

        cat_objs = {}
        for cat_name, skill_names in categories:
            cat, _ = SkillCategory.objects.get_or_create(name=cat_name, defaults={"description": f"{cat_name} category"})
            cat_objs[cat_name] = cat
            for s in skill_names:
                Skill.objects.get_or_create(category=cat, name=s)

        # Users (admin, client, workers)
        admin, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@example.com",
                "first_name": "Site",
                "last_name": "Admin",
                "user_type": "ADMIN",
                "is_staff": True,
                "is_superuser": True,
                "location": "Lagos, Nigeria",
            },
        )
        admin.set_password("admin123")
        admin.save()

        client, _ = User.objects.get_or_create(
            username="client1",
            defaults={
                "email": "client1@example.com",
                "first_name": "Ada",
                "last_name": "Okoro",
                "user_type": "CLIENT",
                "location": "Lagos, Nigeria",
            },
        )
        client.set_password("client123")
        client.save()

        worker_users_data = [
            ("worker1", "Emeka", "Ibrahim", "WORKER", "Ikeja, Lagos, Nigeria"),
            ("worker2", "Zainab", "Lawal", "WORKER", "Yaba, Lagos, Nigeria"),
            ("worker3", "Chinedu", "Eze", "WORKER", "Abuja, Nigeria"),
        ]

        worker_profiles = []
        for uname, first, last, utype, loc in worker_users_data:
            u, _ = User.objects.get_or_create(
                username=uname,
                defaults={
                    "email": f"{uname}@example.com",
                    "first_name": first,
                    "last_name": last,
                    "user_type": utype,
                    "location": loc,
                },
            )
            u.set_password("worker123")
            u.save()
            wp, _ = WorkerProfile.objects.get_or_create(user=u)
            wp.experience_level = "INTERMEDIATE"
            wp.hourly_rate = 20
            wp.is_available = True
            wp.background_verified = True
            wp.is_approved = True
            wp.save()
            worker_profiles.append(wp)

        # Assign skills to workers
        plumbing = Skill.objects.get(category=cat_objs["Home Services"], name="Plumbing")
        electrical = Skill.objects.get(category=cat_objs["Home Services"], name="Electrical")
        webdev = Skill.objects.get(category=cat_objs["Tech & IT"], name="Web Development")
        design = Skill.objects.get(category=cat_objs["Design & Creative"], name="Graphic Design")

        WorkerSkill.objects.get_or_create(worker=worker_profiles[0], skill=plumbing, defaults={"proficiency": "ADVANCED", "years_experience": 4})
        WorkerSkill.objects.get_or_create(worker=worker_profiles[0], skill=electrical, defaults={"proficiency": "INTERMEDIATE", "years_experience": 2})
        WorkerSkill.objects.get_or_create(worker=worker_profiles[1], skill=webdev, defaults={"proficiency": "EXPERT", "years_experience": 5})
        WorkerSkill.objects.get_or_create(worker=worker_profiles[1], skill=design, defaults={"proficiency": "INTERMEDIATE", "years_experience": 3})
        WorkerSkill.objects.get_or_create(worker=worker_profiles[2], skill=plumbing, defaults={"proficiency": "INTERMEDIATE", "years_experience": 3})

        # Jobs (approved/open and one completed)
        job1, _ = Job.objects.get_or_create(
            client=client,
            title="Fix kitchen sink leak",
            defaults={
                "description": "Need a plumber to fix a small leak in the kitchen sink.",
                "location": "Ikeja, Lagos, Nigeria",
                "address": "12 Isaac John St, Ikeja",
                "budget_min": 30,
                "budget_max": 80,
                "estimated_duration": 2,
                "priority": "MEDIUM",
                "status": "OPEN",
                "is_approved": True,
            },
        )
        job1.required_skills.set([plumbing])

        job2, _ = Job.objects.get_or_create(
            client=client,
            title="Install new ceiling light",
            defaults={
                "description": "Install a modern LED ceiling light in the living room.",
                "location": "Yaba, Lagos, Nigeria",
                "address": "3 Herbert Macaulay Way, Yaba",
                "budget_min": 40,
                "budget_max": 120,
                "estimated_duration": 3,
                "priority": "HIGH",
                "status": "OPEN",
                "is_approved": True,
            },
        )
        job2.required_skills.set([electrical])

        job3, _ = Job.objects.get_or_create(
            client=client,
            title="Company landing page (Next.js)",
            defaults={
                "description": "Build a fast, responsive landing page for our startup.",
                "location": "Lagos, Nigeria",
                "address": "Victoria Island",
                "budget_min": 300,
                "budget_max": 800,
                "estimated_duration": 20,
                "priority": "URGENT",
                "status": "OPEN",
                "is_approved": True,
            },
        )
        job3.required_skills.set([webdev, design])

        # Create an application and assign a job
        app1, _ = JobApplication.objects.get_or_create(job=job1, worker=worker_profiles[0], defaults={"status": "PENDING", "proposed_rate": 18})
        # Accept and complete a job for rating demo
        job_completed, _ = Job.objects.get_or_create(
            client=client,
            title="Fix bathroom tap",
            defaults={
                "description": "Tap replacement and minor leak fix.",
                "location": "Ikeja, Lagos, Nigeria",
                "address": "Allen Avenue",
                "budget_min": 20,
                "budget_max": 60,
                "estimated_duration": 2,
                "priority": "LOW",
                "status": "COMPLETED",
                "is_approved": True,
                "completed_at": timezone.now(),
            },
        )
        job_completed.required_skills.set([plumbing])
        job_completed.assigned_worker = worker_profiles[0]
        job_completed.save()

        # Ratings to seed worker stats
        Rating.objects.get_or_create(job=job_completed, rater=client, ratee=worker_profiles[0].user, rating_type='CLIENT_TO_WORKER', defaults={'stars': 5, 'comment': 'Great job, quick and tidy!'})

        # Recompute worker rating aggregates
        for wp in worker_profiles:
            agg = Rating.objects.filter(ratee=wp.user, rating_type='CLIENT_TO_WORKER').aggregate(avg_stars=__import__('django').db.models.Avg('stars'), count=__import__('django').db.models.Count('id'))
            wp.rating = float(agg['avg_stars'] or 0.0)
            wp.num_ratings = int(agg['count'] or 0)
            wp.is_approved = True
            wp.save()

        self.stdout.write(self.style.SUCCESS("Demo data seeded.\nUsers:\n - admin / admin123\n - client1 / client123\n - worker1 / worker123\n - worker2 / worker123\n - worker3 / worker123"))


