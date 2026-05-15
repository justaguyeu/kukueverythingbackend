from django.urls import path
from .views import ReviewListView, ReviewCreateView, ReviewHelpfulView, MyReviewsView

urlpatterns = [
    path('', ReviewCreateView.as_view(), name='review-create'),
    path('my-reviews/', MyReviewsView.as_view(), name='my-reviews'),
    path('business/<int:business_id>/', ReviewListView.as_view(), name='business-reviews'),
    path('<int:pk>/helpful/', ReviewHelpfulView.as_view(), name='review-helpful'),
]
