from rest_framework import serializers
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    reviewer_display = serializers.SerializerMethodField()

    class Meta:
        model = Review
        fields = [
            'id', 'business', 'reviewer_display', 'reviewer_name',
            'rating', 'title', 'comment', 'helpful_count',
            'is_approved', 'created_at',
        ]
        read_only_fields = ['id', 'helpful_count', 'is_approved', 'created_at']

    def get_reviewer_display(self, obj):
        if obj.reviewer:
            return obj.reviewer.full_name
        return obj.reviewer_name

    def create(self, validated_data):
        user = self.context['request'].user
        if user.is_authenticated:
            validated_data['reviewer'] = user
            if not validated_data.get('reviewer_name'):
                validated_data['reviewer_name'] = user.full_name
        return super().create(validated_data)


class ReviewCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = ['business', 'reviewer_name', 'reviewer_phone', 'rating', 'title', 'comment']

    def validate_reviewer_name(self, value):
        if not value.strip():
            raise serializers.ValidationError('Reviewer name is required.')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        if user.is_authenticated:
            validated_data['reviewer'] = user
            if not validated_data.get('reviewer_name'):
                validated_data['reviewer_name'] = user.full_name
        return super().create(validated_data)
