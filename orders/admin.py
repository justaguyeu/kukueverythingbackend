from django.contrib import admin
from .models import Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display  = ['id', 'customer_name', 'customer_phone', 'business',
                     'product_name', 'quantity', 'total_amount', 'status', 'created_at']
    list_filter   = ['status', 'contact_method', 'created_at', 'business__region']
    search_fields = ['customer_name', 'customer_phone', 'customer_email',
                     'business__name', 'product_name']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at', 'total_amount']

    fieldsets = (
        ('Customer Info', {
            'fields': ('customer', 'customer_name', 'customer_phone',
                       'customer_email', 'customer_region')
        }),
        ('Order Info', {
            'fields': ('business', 'product', 'product_name', 'quantity',
                       'unit_price', 'total_amount')
        }),
        ('Delivery & Notes', {
            'fields': ('delivery_address', 'notes', 'contact_method')
        }),
        ('Status & Dates', {
            'fields': ('status', 'created_at', 'updated_at')
        }),
    )
