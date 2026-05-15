from django.contrib import admin
from .models import Business, BusinessProduct


class BusinessProductInline(admin.TabularInline):
    model = BusinessProduct
    extra = 1


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'region', 'average_rating', 'total_ratings', 'is_verified', 'is_active', 'created_at']
    list_filter = ['region', 'is_verified', 'is_active']
    search_fields = ['name', 'owner__email', 'owner__first_name']
    list_editable = ['is_verified', 'is_active']
    inlines = [BusinessProductInline]
    readonly_fields = ['average_rating', 'total_ratings', 'created_at', 'updated_at']


@admin.register(BusinessProduct)
class BusinessProductAdmin(admin.ModelAdmin):
    list_display = ['business', 'product_type', 'price', 'available']
    list_filter = ['product_type', 'available']
