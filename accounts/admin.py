from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'matriculation_number',
        'expected_graduation_year',
        'user_type',
        'is_verified',
        'has_listed_skill',
        'subscription_active',
        'is_staff',
        'is_active',
    )
    list_filter = (
        'user_type',
        'is_verified',
        'has_listed_skill',
        'subscription_active',
        'is_staff',
        'is_active',
        'created_at',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'matriculation_number')
    ordering = ('-created_at',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (
            'Personal info',
            {
                'fields': (
                    'first_name',
                    'last_name',
                    'email',
                    'phone',
                    'matriculation_number',
                    'expected_graduation_year',
                    'profile_picture',
                    'location',
                    'address',
                )
            },
        ),
        (
            'Account & access',
            {
                'fields': (
                    'user_type',
                    'is_verified',
                    'has_listed_skill',
                    'subscription_active',
                    'subscription_expires_at',
                )
            },
        ),
        (
            'Permissions',
            {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')},
        ),
        (
            'Important dates',
            {'fields': ('last_login', 'date_joined', 'created_at', 'updated_at')},
        ),
    )

    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'username',
                    'email',
                    'first_name',
                    'last_name',
                    'user_type',
                    'password1',
                    'password2',
                ),
            },
        ),
    )

    readonly_fields = ('created_at', 'updated_at')
