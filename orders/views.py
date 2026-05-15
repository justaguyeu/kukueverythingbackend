import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from .models import Order
from .serializers import OrderCreateSerializer, OrderSerializer, OrderStatusUpdateSerializer

logger = logging.getLogger(__name__)


class OrderCreateView(generics.CreateAPIView):
    """
    POST /api/orders/
    Creates an order (guest or logged-in user).
    Immediately fires SMS + Email to the business owner.
    """
    serializer_class = OrderCreateSerializer
    permission_classes = [AllowAny]

    def perform_create(self, serializer):
        order = serializer.save()
        # ── Notify owner ──────────────────────────────────────
        try:
            from notifications.service import notify_owner_new_order
            notify_owner_new_order(order)
        except Exception as e:
            logger.error(f"[OrderCreate] Notification failed: {e}")

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Return full order data, not just the create fields
        order = Order.objects.get(pk=serializer.instance.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class MyOrdersView(generics.ListAPIView):
    """GET /api/orders/my-orders/ — logged-in customer's orders."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).select_related(
            'business', 'product'
        )


class BusinessOrderListView(generics.ListAPIView):
    """GET /api/orders/business/?status=pending — business owner's orders."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            business     = self.request.user.business
            status_param = self.request.query_params.get('status')
            qs = Order.objects.filter(business=business).select_related(
                'business', 'product', 'customer'
            )
            if status_param:
                qs = qs.filter(status=status_param)
            return qs
        except Exception:
            return Order.objects.none()


class BusinessOrderDetailView(generics.RetrieveAPIView):
    """GET /api/orders/business/<pk>/ — full detail of a single order."""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            return Order.objects.filter(
                business=self.request.user.business
            ).select_related('business', 'product', 'customer')
        except Exception:
            return Order.objects.none()


class OrderUpdateStatusView(generics.UpdateAPIView):
    """
    PATCH /api/orders/<pk>/status/
    Business owner updates order status.
    Fires SMS + Email to customer after change.
    """
    serializer_class = OrderStatusUpdateSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            return Order.objects.filter(business=self.request.user.business)
        except Exception:
            return Order.objects.none()

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        old_status = instance.status

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()

        # ── Notify customer if status actually changed ────────
        if order.status != old_status:
            try:
                from notifications.service import notify_customer_status_update
                notify_customer_status_update(order)
            except Exception as e:
                logger.error(f"[StatusUpdate] Notification failed: {e}")

        return Response(OrderSerializer(order).data)
