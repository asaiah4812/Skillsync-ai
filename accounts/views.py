from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetDoneView
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth import get_user_model
from .forms import UserRegistrationForm, UserLoginForm, CustomPasswordResetForm, CustomSetPasswordForm


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            
            # Try to authenticate with username first, then email
            user = authenticate(username=username, password=password)
            if user is None:
                # Try with email
                try:
                    from .models import User
                    user_obj = User.objects.get(email=username)
                    user = authenticate(username=user_obj.username, password=password)
                except User.DoesNotExist:
                    pass
            
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.get_full_name()}!')
                # Redirect to next parameter or dashboard
                next_url = request.GET.get('next', 'core:home')
                return redirect(next_url)
            else:
                messages.error(request, 'Invalid username/email or password.')
    else:
        form = UserLoginForm()
    
    return render(request, 'account/login.html', {'form': form})


def register_view(request):
    """Handle user registration"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f'Welcome to SkillSync, {user.get_full_name()}! Your account has been created successfully.')
            return redirect('core:home')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'account/signup.html', {'form': form})


@login_required
def logout_view(request):
    """Handle user logout"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('core:home')


@login_required
def profile_view(request):
    """Display user profile"""
    return render(request, 'account/profile.html', {'user': request.user})


class CustomPasswordResetView(PasswordResetView):
    """Custom password reset view with styled form"""
    template_name = 'account/password_reset.html'
    email_template_name = 'account/password_reset_email.html'
    subject_template_name = 'account/password_reset_subject.txt'
    form_class = CustomPasswordResetForm
    success_url = '/accounts/password-reset/done/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Password reset email has been sent. Please check your email.')
        return super().form_valid(form)


class CustomPasswordResetDoneView(PasswordResetDoneView):
    """Custom password reset done view"""
    template_name = 'account/password_reset_done.html'


class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    """Custom password reset confirm view with styled form"""
    template_name = 'account/password_reset_confirm.html'
    form_class = CustomSetPasswordForm
    success_url = '/accounts/password-reset/complete/'
    
    def form_valid(self, form):
        messages.success(self.request, 'Your password has been reset successfully. You can now log in with your new password.')
        return super().form_valid(form)


class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    """Custom password reset complete view"""
    template_name = 'account/password_reset_complete.html'