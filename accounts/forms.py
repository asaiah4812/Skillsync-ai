from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth import authenticate
from .models import User


class UserRegistrationForm(UserCreationForm):
    """Custom registration form with additional fields"""
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Enter your email'
    }))
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'First name'
    }))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Last name'
    }))
    phone = forms.CharField(max_length=20, required=False, widget=forms.TextInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Phone number (optional)'
    }))
    user_type = forms.ChoiceField(choices=User.USER_TYPES, widget=forms.Select(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm'
    }))
    
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Enter your password'
    }))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Confirm your password'
    }))

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'user_type', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({
            'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
            'placeholder': 'Choose a username'
        })


class ProfileUpdateForm(forms.ModelForm):
    """Form for updating user profile information"""
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'phone')
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
                'placeholder': 'First name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
                'placeholder': 'Last name'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
                'placeholder': 'Email address'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
                'placeholder': 'Phone number'
            }),
        }


class UserLoginForm(AuthenticationForm):
    """Custom login form with styled widgets"""
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Enter your username or email'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Enter your password'
    }))
    
    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')
        
        if username and password:
            # Try to authenticate with username first, then email
            user = authenticate(username=username, password=password)
            if user is None:
                # Try with email
                try:
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is None:
                raise forms.ValidationError('Invalid username/email or password.')
            elif not user.is_active:
                raise forms.ValidationError('This account is inactive.')
        
        return self.cleaned_data


class CustomPasswordResetForm(PasswordResetForm):
    """Custom password reset form with styled widgets"""
    email = forms.EmailField(widget=forms.EmailInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Enter your email address'
    }))


class CustomSetPasswordForm(SetPasswordForm):
    """Custom set password form with styled widgets"""
    new_password1 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Enter new password'
    }))
    new_password2 = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent dark:bg-gray-700 dark:text-white text-sm',
        'placeholder': 'Confirm new password'
    }))
