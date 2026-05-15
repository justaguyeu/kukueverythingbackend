from django.urls import path
from .views import (
    OrderCreateView,
    MyOrdersView,
    BusinessOrderListView,
    BusinessOrderDetailView,
    OrderUpdateStatusView,
)

urlpatterns = [
    path('',                   OrderCreateView.as_view(),        name='order-create'),
    path('my-orders/',         MyOrdersView.as_view(),           name='my-orders'),
    path('business/',          BusinessOrderListView.as_view(),   name='business-orders'),
    path('business/<int:pk>/', BusinessOrderDetailView.as_view(), name='business-order-detail'),
    path('<int:pk>/status/',   OrderUpdateStatusView.as_view(),   name='order-status-update'),
]
