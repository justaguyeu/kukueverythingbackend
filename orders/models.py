from django.db import models
from django.conf import settings


ORDER_STATUS = [
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('confirmed', 'Confirmed'),
    ('completed', 'Completed'),
    ('cancelled', 'Cancelled'),
]

CONTACT_METHOD = [
    ('online', 'Online Order'),
    ('whatsapp', 'WhatsApp'),
    ('call', 'Phone Call'),
]


class Order(models.Model):
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders'
    )
    # For guest orders (non-logged-in users)
    customer_name = models.CharField(max_length=200)
    customer_phone = models.CharField(max_length=20)
    customer_email = models.EmailField(blank=True)
    customer_region = models.CharField(max_length=100, blank=True)

    product = models.ForeignKey(
        'businesses.BusinessProduct',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='orders'
    )
    product_name = models.CharField(max_length=200)  # Snapshot at order time
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    delivery_address = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    contact_method = models.CharField(max_length=20, choices=CONTACT_METHOD, default='online')
    status = models.CharField(max_length=20, choices=ORDER_STATUS, default='pending', db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Order #{self.pk} - {self.customer_name} → {self.business.name}"

    def save(self, *args, **kwargs):
        if self.unit_price and self.quantity:
            self.total_amount = self.unit_price * self.quantity
        super().save(*args, **kwargs)
