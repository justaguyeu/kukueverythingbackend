from django.urls import path
from .views import (
    BusinessListView, BusinessCreateView, BusinessDetailView,
    MyBusinessView, RegionListView, TopBusinessesByRegionView,
    BusinessProductView, DashboardStatsView,
)

urlpatterns = [
    path('', BusinessListView.as_view(), name='business-list'),
    path('register/', BusinessCreateView.as_view(), name='business-create'),
    path('my-business/', MyBusinessView.as_view(), name='my-business'),
    path('my-business/dashboard/', DashboardStatsView.as_view(), name='dashboard-stats'),
    path('regions/', RegionListView.as_view(), name='region-list'),
    path('top/', TopBusinessesByRegionView.as_view(), name='top-businesses'),
    path('<int:pk>/', BusinessDetailView.as_view(), name='business-detail'),
    path('<int:pk>/products/', BusinessProductView.as_view(), name='business-products'),
]
