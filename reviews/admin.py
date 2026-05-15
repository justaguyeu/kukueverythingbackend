from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['reviewer_name', 'business', 'rating', 'title', 'is_approved', 'created_at']
    list_filter = ['rating', 'is_approved', 'created_at']
    search_fields = ['reviewer_name', 'business__name', 'comment']
    list_editable = ['is_approved']
    readonly_fields = ['created_at', 'updated_at']
