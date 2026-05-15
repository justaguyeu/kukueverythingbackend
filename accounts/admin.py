from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'full_name', 'is_business_owner', 'is_staff', 'created_at']
    list_filter = ['is_business_owner', 'is_staff', 'is_active']
    search_fields = ['email', 'first_name', 'last_name', 'phone']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('Extra', {'fields': ('phone', 'is_business_owner')}),
    )
