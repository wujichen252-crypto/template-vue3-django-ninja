"""Django admin configuration for users."""
from django.contrib import admin
from apps.users.models import User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """User admin configuration."""
    list_display = ['id', 'username', 'email', 'status', 'created_at']
    list_filter = ['status', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email']
    ordering = ['-created_at']
