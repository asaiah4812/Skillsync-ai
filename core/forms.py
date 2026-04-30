from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Job, JobApplication, WorkerProfile, Skill, SkillCategory, LearningInterest


class JobForm(forms.ModelForm):
    """Form for creating and editing skill requests"""
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'required_skills', 'location', 'address',
            'budget_min', 'budget_max', 'estimated_duration', 'priority',
            'scheduled_for'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'Enter request title'
            }),
            'description': forms.Textarea(attrs={
                'class': 'ss-input w-full',
                'rows': 4,
                'placeholder': 'Describe what you need help learning/doing'
            }),
            'location': forms.TextInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'City, State or coordinates'
            }),
            'address': forms.Textarea(attrs={
                'class': 'ss-input w-full',
                'rows': 3,
                'placeholder': 'Full address where the work will be done'
            }),
            'budget_min': forms.NumberInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'Minimum budget'
            }),
            'budget_max': forms.NumberInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'Maximum budget'
            }),
            'estimated_duration': forms.NumberInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'Estimated hours'
            }),
            'priority': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'scheduled_for': forms.DateTimeInput(attrs={
                'class': 'ss-input w-full',
                'type': 'datetime-local'
            }),
            'required_skills': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active skills only
        self.fields['required_skills'].queryset = Skill.objects.filter(is_active=True)


class JobApplicationForm(forms.ModelForm):
    """Form for students to respond to requests"""
    class Meta:
        model = JobApplication
        fields = ['cover_letter', 'proposed_rate', 'estimated_completion']
        widgets = {
            'cover_letter': forms.Textarea(attrs={
                'class': 'ss-input w-full',
                'rows': 4,
                'placeholder': 'Explain how you can help with this request...'
            }),
            'proposed_rate': forms.NumberInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'Your proposed hourly rate'
            }),
            'estimated_completion': forms.DateTimeInput(attrs={
                'class': 'ss-input w-full',
                'type': 'datetime-local'
            })
        }


class WorkerProfileForm(forms.ModelForm):
    """Form for workers to update their profile"""
    skills_to_learn = forms.ModelMultipleChoiceField(
        queryset=Skill.objects.filter(is_active=True),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        }),
        help_text="Select skills you want to learn. Hold Ctrl/Cmd to select multiple.",
    )

    class Meta:
        model = WorkerProfile
        fields = [
            'bio', 'skills', 'experience_level', 'hourly_rate', 'is_available'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'ss-input w-full',
                'rows': 4,
                'placeholder': 'Tell clients about your experience and expertise...'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'Your hourly rate'
            }),
            'experience_level': forms.Select(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            }),
            'is_available': forms.CheckboxInput(attrs={
                'class': 'rounded border-gray-300'
            }),
            'skills': forms.SelectMultiple(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filter active skills only
        self.fields['skills'].queryset = Skill.objects.filter(is_active=True)
        if self.instance and getattr(self.instance, 'user_id', None):
            self.fields['skills_to_learn'].initial = LearningInterest.objects.filter(
                user_id=self.instance.user_id
            ).values_list('skill_id', flat=True)

    def save(self, commit=True):
        profile = super().save(commit=commit)
        # Update learning interests for this user
        skill_ids = []
        if self.cleaned_data.get('skills_to_learn') is not None:
            skill_ids = list(self.cleaned_data['skills_to_learn'].values_list('id', flat=True))
        LearningInterest.objects.filter(user=profile.user).exclude(skill_id__in=skill_ids).delete()
        existing = set(LearningInterest.objects.filter(user=profile.user).values_list('skill_id', flat=True))
        to_create = [LearningInterest(user=profile.user, skill_id=sid) for sid in skill_ids if sid not in existing]
        if to_create:
            LearningInterest.objects.bulk_create(to_create)
        return profile


class JobSearchForm(forms.Form):
    """Form for searching skill requests"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Search requests...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=SkillCategory.objects.filter(is_active=True),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    location = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Location'
        })
    )
    budget_min = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Min budget'
        })
    )
    budget_max = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Max budget'
        })
    )


class WorkerSearchForm(forms.Form):
    """Form for searching workers"""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Search workers...'
        })
    )
    skill = forms.ModelChoiceField(
        queryset=Skill.objects.filter(is_active=True),
        required=False,
        empty_label="All Skills",
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    experience_level = forms.ChoiceField(
        choices=[('', 'All Experience Levels')] + WorkerProfile.EXPERIENCE_LEVELS,
        required=False,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent'
        })
    )
    max_rate = forms.DecimalField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent',
            'placeholder': 'Max hourly rate'
        })
    )
