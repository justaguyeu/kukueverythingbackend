from django.contrib import admin
from .models import Business, BusinessProduct, BusinessRegion


class BusinessProductInline(admin.TabularInline):
    model = BusinessProduct
    extra = 1


class BusinessRegionInline(admin.TabularInline):
    model  = BusinessRegion
    extra  = 1
    verbose_name        = 'Extra Region'
    verbose_name_plural = 'Extra Regions (beyond primary)'


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
    list_display   = ['name', 'owner', 'region', 'average_rating', 'total_ratings', 'is_verified', 'is_active', 'created_at']
    list_filter    = ['region', 'is_verified', 'is_active']
    search_fields  = ['name', 'owner__email', 'owner__first_name']
    list_editable  = ['is_verified', 'is_active']
    inlines        = [BusinessRegionInline, BusinessProductInline]
    readonly_fields = ['average_rating', 'total_ratings', 'created_at', 'updated_at']


@admin.register(BusinessRegion)
class BusinessRegionAdmin(admin.ModelAdmin):
    list_display  = ['business', 'region']
    list_filter   = ['region']
    search_fields = ['business__name']


@admin.register(BusinessProduct)
class BusinessProductAdmin(admin.ModelAdmin):
    list_display = ['business', 'product_type', 'price', 'available']
    list_filter  = ['product_type', 'available']
