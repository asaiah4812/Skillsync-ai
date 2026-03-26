from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.views import PasswordResetView, PasswordResetConfirmView, PasswordResetCompleteView, PasswordResetDoneView
from .forms import UserRegistrationForm, UserLoginForm, CustomPasswordResetForm, CustomSetPasswordForm


def login_view(request):
    """Handle user login"""
    if request.user.is_authenticated:
        return redirect('core:home')
    
    if request.method == 'POST':
        form = UserLoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            display = user.get_full_name() or user.username
            messages.success(request, f'Welcome back, {display}!')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:home')
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
            messages.success(
                request,
                f'Welcome to SkillSwap, {user.username}! Your FUK student account is ready.'
            )
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