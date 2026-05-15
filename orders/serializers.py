from rest_framework import serializers
from .models import Order


class OrderCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = [
            'business', 'product', 'product_name', 'quantity',
            'customer_name', 'customer_phone', 'customer_email',
            'customer_region', 'delivery_address', 'notes', 'contact_method',
        ]

    def create(self, validated_data):
        user = self.context['request'].user
        if user.is_authenticated:
            validated_data['customer'] = user
        product = validated_data.get('product')
        if product and product.price:
            validated_data['unit_price'] = product.price
        return super().create(validated_data)


class OrderSerializer(serializers.ModelSerializer):
    """Full serializer — every field visible in dashboard order detail."""
    business_name   = serializers.CharField(source='business.name',   read_only=True)
    business_region = serializers.CharField(source='business.region', read_only=True)
    business_phone  = serializers.CharField(source='business.phone',  read_only=True)
    product_display = serializers.SerializerMethodField()
    contact_method_display = serializers.CharField(
        source='get_contact_method_display', read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', read_only=True
    )

    class Meta:
        model = Order
        fields = [
            # IDs
            'id',
            # Business info
            'business', 'business_name', 'business_region', 'business_phone',
            # Product
            'product', 'product_display', 'product_name',
            'quantity', 'unit_price', 'total_amount',
            # Customer info  ← all shown in dashboard order detail
            'customer_name', 'customer_phone', 'customer_email',
            'customer_region', 'delivery_address', 'notes',
            # Meta
            'contact_method', 'contact_method_display',
            'status', 'status_display',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']

    def get_product_display(self, obj):
        if obj.product:
            return obj.product.get_product_type_display()
        return obj.product_name


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']
