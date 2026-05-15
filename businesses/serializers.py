from rest_framework import serializers
from .models import Business, BusinessProduct


class BusinessProductSerializer(serializers.ModelSerializer):
    product_type_display = serializers.CharField(source='get_product_type_display', read_only=True)

    class Meta:
        model = BusinessProduct
        fields = ['id', 'product_type', 'product_type_display', 'price', 'price_unit', 'available', 'description']


class BusinessListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views."""
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    products = BusinessProductSerializer(many=True, read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'owner_name', 'region', 'phone', 'whatsapp',
            'description', 'logo_url', 'is_verified', 'average_rating',
            'total_ratings', 'products', 'created_at',
        ]

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None


class BusinessDetailSerializer(serializers.ModelSerializer):
    """Full serializer for detail views."""
    owner_name = serializers.CharField(source='owner.full_name', read_only=True)
    owner_email = serializers.CharField(source='owner.email', read_only=True)
    products = BusinessProductSerializer(many=True, read_only=True)
    logo_url = serializers.SerializerMethodField()

    class Meta:
        model = Business
        fields = [
            'id', 'name', 'owner_name', 'owner_email', 'region', 'address',
            'phone', 'whatsapp', 'description', 'logo_url', 'is_verified',
            'average_rating', 'total_ratings', 'products', 'is_active', 'created_at',
        ]

    def get_logo_url(self, obj):
        request = self.context.get('request')
        if obj.logo and request:
            return request.build_absolute_uri(obj.logo.url)
        return None


class BusinessCreateSerializer(serializers.ModelSerializer):
    products = BusinessProductSerializer(many=True, required=False)

    class Meta:
        model = Business
        fields = [
            'name', 'region', 'address', 'phone', 'whatsapp',
            'description', 'logo', 'products',
        ]

    def create(self, validated_data):
        products_data = validated_data.pop('products', [])
        business = Business.objects.create(owner=self.context['request'].user, **validated_data)
        for product_data in products_data:
            BusinessProduct.objects.create(business=business, **product_data)
        # Mark user as business owner
        user = self.context['request'].user
        user.is_business_owner = True
        user.save(update_fields=['is_business_owner'])
        return business

    def update(self, instance, validated_data):
        products_data = validated_data.pop('products', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if products_data is not None:
            instance.products.all().delete()
            for product_data in products_data:
                BusinessProduct.objects.create(business=instance, **product_data)
        return instance


class RegionTopSerializer(serializers.Serializer):
    """For returning top business per region."""
    region = serializers.CharField()
    businesses = BusinessListSerializer(many=True)
