from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .models import Review
from .serializers import ReviewSerializer, ReviewCreateSerializer


class ReviewListView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        business_id = self.kwargs.get('business_id')
        return Review.objects.filter(business_id=business_id, is_approved=True)


class ReviewCreateView(generics.CreateAPIView):
    serializer_class = ReviewCreateSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        review = serializer.save()
        return Response(
            ReviewSerializer(review).data,
            status=status.HTTP_201_CREATED
        )


class ReviewHelpfulView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, pk):
        try:
            review = Review.objects.get(pk=pk, is_approved=True)
            review.helpful_count += 1
            review.save(update_fields=['helpful_count'])
            return Response({'helpful_count': review.helpful_count})
        except Review.DoesNotExist:
            return Response({'error': 'Review not found.'}, status=404)


class MyReviewsView(generics.ListAPIView):
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Review.objects.filter(reviewer=self.request.user)
