from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator


REGION_LIST = [
    'Arusha', 'Dar es Salaam', 'Dodoma', 'Geita', 'Iringa',
    'Kagera', 'Katavi', 'Kigoma', 'Kilimanjaro', 'Lindi',
    'Manyara', 'Mara', 'Mbeya', 'Mjini Magharibi', 'Morogoro',
    'Mtwara', 'Mwanza', 'Njombe', 'Pemba Kaskazini', 'Pemba Kusini',
    'Pwani', 'Rukwa', 'Ruvuma', 'Shinyanga', 'Simiyu',
    'Singida', 'Songwe', 'Tabora', 'Tanga', 'Unguja Kaskazini',
    'Unguja Kusini',
]
REGION_CHOICES = [(r, r) for r in REGION_LIST]

PRODUCT_CHOICES = [
    ('kuku_kienyeji_live', 'Kuku wa Kienyeji (Live)'),
    ('kuku_kisasa_live',   'Kuku wa Kisasa (Live)'),
    ('nyama_kienyeji',     'Nyama ya Kuku Kienyeji'),
    ('nyama_kisasa',       'Nyama ya Kuku Kisasa'),
    ('mayai_kienyeji',     'Mayai ya Kienyeji'),
    ('mayai_kisasa',       'Mayai ya Kisasa'),
]


class Business(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='business'
    )
    name        = models.CharField(max_length=200, unique=True)
    # Primary region kept for backward compatibility + top-seller-per-region queries
    region      = models.CharField(max_length=100, choices=REGION_CHOICES, db_index=True)
    address     = models.TextField(blank=True)
    phone       = models.CharField(max_length=20)
    whatsapp    = models.CharField(max_length=20, blank=True)
    description = models.TextField(blank=True)
    logo        = models.ImageField(upload_to='business_logos/', blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_active   = models.BooleanField(default=True)

    average_rating = models.DecimalField(
        max_digits=3, decimal_places=2, default=0.00,
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    total_ratings = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Business'
        verbose_name_plural = 'Businesses'
        ordering = ['-average_rating', '-total_ratings', 'name']

    def __str__(self):
        return f"{self.name} ({self.region})"

    @property
    def all_regions(self):
        """All regions this business serves (primary + extra)."""
        extra = list(self.extra_regions.values_list('region', flat=True))
        regions = [self.region] + [r for r in extra if r != self.region]
        return regions

    def update_rating(self):
        from reviews.models import Review
        reviews = Review.objects.filter(business=self, is_approved=True)
        count   = reviews.count()
        if count > 0:
            total = sum(r.rating for r in reviews)
            self.average_rating = round(total / count, 2)
        else:
            self.average_rating = 0.00
        self.total_ratings = count
        self.save(update_fields=['average_rating', 'total_ratings'])


class BusinessRegion(models.Model):
    """Extra regions a business operates in (beyond its primary region)."""
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='extra_regions')
    region   = models.CharField(max_length=100, choices=REGION_CHOICES, db_index=True)

    class Meta:
        unique_together = ['business', 'region']

    def __str__(self):
        return f"{self.business.name} → {self.region}"


class BusinessProduct(models.Model):
    business     = models.ForeignKey(Business, on_delete=models.CASCADE, related_name='products')
    product_type = models.CharField(max_length=50, choices=PRODUCT_CHOICES)
    price        = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    price_unit   = models.CharField(max_length=50, blank=True)
    available    = models.BooleanField(default=True)
    description  = models.TextField(blank=True)

    class Meta:
        unique_together = ['business', 'product_type']

    def __str__(self):
        return f"{self.business.name} - {self.get_product_type_display()}"
