from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
import re
from .models import User


class UserRegistrationForm(UserCreationForm):
    """Student registration form."""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'ss-input w-full',
        'placeholder': 'Enter your email address'
    }))
    matriculation_number = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'ss-input w-full',
        'placeholder': 'e.g. FUKU/SCI/21B/COM/0120'
    }))
    
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'ss-input w-full',
        'placeholder': 'Enter your password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'ss-input w-full',
        'placeholder': 'Confirm your password'
    }))

    class Meta:
        model = User
        fields = ('username', 'email', 'matriculation_number', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'ss-input w-full',
            'placeholder': 'Choose a username'
        })

    def clean_email(self):
        # No university-domain restriction; just normalize.
        return self.cleaned_data['email'].strip().lower()

    def clean_matriculation_number(self):
        matric = self.cleaned_data['matriculation_number'].strip().upper().replace(' ', '')
        # Examples:
        # - FUKU/SCI/21B/COM/0120
        # - FUKD/SCI/22/ZOO/001
        # - FUKU/SCI/22/MCB/0085
        if not re.match(r'^FUK[UD]/[A-Z]{2,10}/\d{2}[A-Z]?/[A-Z]{2,10}/\d{2,6}$', matric):
            raise ValidationError('Enter a valid matriculation number format.')
        if User.objects.filter(matriculation_number=matric).exists():
            raise ValidationError('This matriculation number is already registered.')
        return matric


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'Email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'ss-input w-full',
                'placeholder': 'Phone number'
            }),
        }


def _user_from_login_identifier(raw):
    """Resolve login field to a User by email, username, or matriculation number."""
    raw = (raw or '').strip()
    if not raw:
        return None
    # University email (case-insensitive)
    u = User.objects.filter(email__iexact=raw).first()
    if u:
        return u
    # Username (case-insensitive)
    u = User.objects.filter(username__iexact=raw).first()
    if u:
        return u
    # Matriculation number (stored uppercase, e.g. FUK/CSC/20/1234)
    matric = raw.upper().replace(' ', '')
    return User.objects.filter(matriculation_number=matric).first()


class UserLoginForm(AuthenticationForm):
    """Login with university email, username, or matriculation number + password."""
    username = forms.CharField(
        label='Login',
        widget=forms.TextInput(attrs={
            'class': 'ss-input w-full',
            'placeholder': 'Email, username, or matric number',
            'autocomplete': 'username',
        }),
    )
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'ss-input w-full',
        'placeholder': 'Enter your password',
        'autocomplete': 'current-password',
    }))

    def clean(self):
        identifier = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if identifier is not None:
            identifier = identifier.strip()
        if not identifier or not password:
            raise forms.ValidationError('Please enter both login and password.')

        user_obj = _user_from_login_identifier(identifier)
        if user_obj is None:
            raise forms.ValidationError('Invalid login or password.')

        user = authenticate(request=self.request, username=user_obj.username, password=password)
        if user is None:
            raise forms.ValidationError('Invalid login or password.')

        self.user_cache = user
        self.confirm_login_allowed(user)
        return self.cleaned_data


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with styled widgets"""
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'ss-input w-full',
        'placeholder': 'Enter your email address'
    }))


class CustomSetPasswordForm(SetPasswordForm):
    """Custom set password form with styled widgets"""
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'ss-input w-full',
        'placeholder': 'Enter new password'
    }))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'ss-input w-full',
        'placeholder': 'Confirm new password'
    }))
