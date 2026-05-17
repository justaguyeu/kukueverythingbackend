import django_filters
from django.db.models import Q
from .models import Business


class BusinessFilter(django_filters.FilterSet):
    region      = django_filters.CharFilter(method='filter_region')
    name        = django_filters.CharFilter(lookup_expr='icontains')
    min_rating  = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    is_verified = django_filters.BooleanFilter()
    product_type = django_filters.CharFilter(field_name='products__product_type', lookup_expr='iexact')

    class Meta:
        model  = Business
        fields = ['region', 'name', 'min_rating', 'is_verified', 'product_type']

    def filter_region(self, queryset, name, value):
        """
        Match businesses whose PRIMARY region OR any EXTRA region matches.
        This allows a business to appear in multiple region searches.
        """
        return queryset.filter(
            Q(region__iexact=value) |
            Q(extra_regions__region__iexact=value)
        ).distinct()
