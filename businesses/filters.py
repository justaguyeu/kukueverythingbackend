import django_filters
from .models import Business


class BusinessFilter(django_filters.FilterSet):
    region = django_filters.CharFilter(lookup_expr='iexact')
    name = django_filters.CharFilter(lookup_expr='icontains')
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    is_verified = django_filters.BooleanFilter()
    product_type = django_filters.CharFilter(field_name='products__product_type', lookup_expr='iexact')

    class Meta:
        model = Business
        fields = ['region', 'name', 'min_rating', 'is_verified', 'product_type']
