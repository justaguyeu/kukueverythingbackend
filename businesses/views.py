from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import Business, BusinessProduct, BusinessRegion, REGION_LIST
from .serializers import (
    BusinessListSerializer, BusinessDetailSerializer,
    BusinessCreateSerializer, BusinessProductSerializer
)
from .filters import BusinessFilter


class BusinessListView(generics.ListAPIView):
    serializer_class   = BusinessListSerializer
    permission_classes = [AllowAny]
    filter_backends    = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class    = BusinessFilter
    search_fields      = ['name', 'region', 'description',
                          'owner__first_name', 'owner__last_name',
                          'extra_regions__region']
    ordering_fields    = ['average_rating', 'total_ratings', 'name', 'created_at']
    ordering           = ['-average_rating', '-total_ratings']

    def get_queryset(self):
        return Business.objects.filter(is_active=True).prefetch_related('products', 'extra_regions')


class BusinessCreateView(generics.CreateAPIView):
    serializer_class   = BusinessCreateSerializer
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        if hasattr(self.request.user, 'business'):
            from rest_framework.exceptions import ValidationError
            raise ValidationError('You already have a registered business.')
        serializer.save()


class BusinessDetailView(generics.RetrieveAPIView):
    queryset           = Business.objects.filter(is_active=True).prefetch_related('products', 'extra_regions')
    serializer_class   = BusinessDetailSerializer
    permission_classes = [AllowAny]


class MyBusinessView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes     = [MultiPartParser, FormParser, JSONParser]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return BusinessCreateSerializer
        return BusinessDetailSerializer

    def get_object(self):
        try:
            return self.request.user.business
        except Business.DoesNotExist:
            from rest_framework.exceptions import NotFound
            raise NotFound('You have not registered a business yet.')


class RegionListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        data = []
        for region in REGION_LIST:
            # Count businesses with this as primary OR extra region
            count = Business.objects.filter(
                Q(region=region) | Q(extra_regions__region=region),
                is_active=True
            ).distinct().count()
            top = Business.objects.filter(
                Q(region=region) | Q(extra_regions__region=region),
                is_active=True
            ).distinct().order_by('-average_rating', '-total_ratings').first()
            data.append({
                'region': region,
                'business_count': count,
                'top_business': BusinessListSerializer(top, context={'request': request}).data if top else None,
            })
        return Response(data)


class TopBusinessesByRegionView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        region = request.query_params.get('region')
        limit  = int(request.query_params.get('limit', 8))
        qs = Business.objects.filter(is_active=True).prefetch_related('products', 'extra_regions')
        if region:
            qs = qs.filter(
                Q(region__iexact=region) | Q(extra_regions__region__iexact=region)
            ).distinct()
        qs = qs.order_by('-average_rating', '-total_ratings')[:limit]
        return Response(BusinessListSerializer(qs, many=True, context={'request': request}).data)


class BusinessProductView(generics.ListCreateAPIView):
    serializer_class   = BusinessProductSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        return BusinessProduct.objects.filter(business_id=self.kwargs['pk'])

    def perform_create(self, serializer):
        serializer.save(business=self.request.user.business)


class DashboardStatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            business = request.user.business
        except Business.DoesNotExist:
            return Response({'error': 'No business found.'}, status=404)

        from orders.models import Order
        from reviews.models import Review

        orders  = Order.objects.filter(business=business)
        reviews = Review.objects.filter(business=business, is_approved=True)

        return Response({
            'business': BusinessDetailSerializer(business, context={'request': request}).data,
            'stats': {
                'total_orders':      orders.count(),
                'pending_orders':    orders.filter(status='pending').count(),
                'completed_orders':  orders.filter(status='completed').count(),
                'processing_orders': orders.filter(status='processing').count(),
                'total_revenue':     str(sum(
                    o.total_amount for o in orders.filter(status='completed') if o.total_amount
                )),
                'total_reviews':  reviews.count(),
                'average_rating': str(business.average_rating),
            }
        })
