from rest_framework import serializers
from .models import Business, BusinessProduct, BusinessRegion


class BusinessProductSerializer(serializers.ModelSerializer):
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)

    class Meta:
        model  = BusinessProduct
        fields = ['id', 'product_type', 'product_type_display', 'price', 'price_unit', 'available', 'description']


class BusinessRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model  = BusinessRegion
        fields = ['id', 'region']


def _logo_url(obj, request):
    if obj.logo and request:
        return request.build_absolute_uri(obj.logo.url)
    return None


class BusinessListSerializer(serializers.ModelSerializer):
    owner_name   = serializers.CharField(source='owner.full_name', read_only=True)
    products     = BusinessProductSerializer(many=True, read_only=True)
    logo_url     = serializers.SerializerMethodField()
    # All regions this business serves
    extra_regions = serializers.SerializerMethodField()
    all_regions   = serializers.SerializerMethodField()

    class Meta:
        model  = Business
        fields = [
            'id', 'name', 'owner_name', 'region', 'extra_regions', 'all_regions',
            'phone', 'whatsapp', 'description', 'logo_url', 'is_verified',
            'average_rating', 'total_ratings', 'products', 'created_at',
        ]

    def get_logo_url(self, obj):
        return _logo_url(obj, self.context.get('request'))

    def get_extra_regions(self, obj):
        return list(obj.extra_regions.values_list('region', flat=True))

    def get_all_regions(self, obj):
        return obj.all_regions


class BusinessDetailSerializer(serializers.ModelSerializer):
    owner_name    = serializers.CharField(source='owner.full_name',  read_only=True)
    owner_email   = serializers.CharField(source='owner.email',      read_only=True)
    products      = BusinessProductSerializer(many=True, read_only=True)
    logo_url      = serializers.SerializerMethodField()
    extra_regions = serializers.SerializerMethodField()
    all_regions   = serializers.SerializerMethodField()

    class Meta:
        model  = Business
        fields = [
            'id', 'name', 'owner_name', 'owner_email',
            'region', 'extra_regions', 'all_regions',
            'address', 'phone', 'whatsapp', 'description',
            'logo_url', 'is_verified', 'average_rating',
            'total_ratings', 'products', 'is_active', 'created_at',
        ]

    def get_logo_url(self, obj):
        return _logo_url(obj, self.context.get('request'))

    def get_extra_regions(self, obj):
        return list(obj.extra_regions.values_list('region', flat=True))

    def get_all_regions(self, obj):
        return obj.all_regions


class BusinessCreateSerializer(serializers.ModelSerializer):
    products      = BusinessProductSerializer(many=True, required=False)
    # Accept comma-separated extra region names e.g. "Arusha,Dodoma"
    extra_regions = serializers.ListField(
        child=serializers.CharField(), required=False, write_only=True
    )

    class Meta:
        model  = Business
        fields = [
            'name', 'region', 'extra_regions', 'address',
            'phone', 'whatsapp', 'description', 'logo', 'products',
        ]

    def create(self, validated_data):
        products_data     = validated_data.pop('products', [])
        extra_regions_data = validated_data.pop('extra_regions', [])

        business = Business.objects.create(owner=self.context['request'].user, **validated_data)

        for product_data in products_data:
            BusinessProduct.objects.create(business=business, **product_data)

        for region_name in extra_regions_data:
            region_name = region_name.strip()
            if region_name and region_name != business.region:
                BusinessRegion.objects.get_or_create(business=business, region=region_name)

        user = self.context['request'].user
        user.is_business_owner = True
        user.save(update_fields=['is_business_owner'])
        return business

    def update(self, instance, validated_data):
        products_data      = validated_data.pop('products', None)
        extra_regions_data = validated_data.pop('extra_regions', None)

        # Handle logo: if a new logo is uploaded use it; if 'clear' is passed remove it
        logo = validated_data.get('logo')
        if logo == '' or logo is None and 'logo' in self.initial_data:
            # keep existing logo unless explicitly new file sent
            validated_data.pop('logo', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if products_data is not None:
            instance.products.all().delete()
            for product_data in products_data:
                BusinessProduct.objects.create(business=instance, **product_data)

        if extra_regions_data is not None:
            instance.extra_regions.all().delete()
            for region_name in extra_regions_data:
                region_name = region_name.strip()
                if region_name and region_name != instance.region:
                    BusinessRegion.objects.get_or_create(business=instance, region=region_name)

        return instance
