from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class Review(models.Model):
    business = models.ForeignKey(
        'businesses.Business',
        on_delete=models.CASCADE,
        related_name='reviews'
    )
    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='reviews_given'
    )
    # For guest reviewers
    reviewer_name = models.CharField(max_length=200)
    reviewer_phone = models.CharField(max_length=20, blank=True)

    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()

    # Related order (optional)
    order = models.OneToOneField(
        'orders.Order',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='review'
    )

    is_approved = models.BooleanField(default=True)  # Auto-approve; can change to False for moderation
    helpful_count = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.reviewer_name} → {self.business.name} ({self.rating}★)"


@receiver(post_save, sender=Review)
def update_business_rating_on_save(sender, instance, **kwargs):
    if instance.business_id:
        instance.business.update_rating()


@receiver(post_delete, sender=Review)
def update_business_rating_on_delete(sender, instance, **kwargs):
    if instance.business_id:
        try:
            instance.business.update_rating()
        except Exception:
            pass
