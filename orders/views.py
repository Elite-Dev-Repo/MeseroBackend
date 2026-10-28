from django.db import models, transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Order, Order_Item
from .serializers import OrderSerializer, OrderStatusUpdateSerializer


def orders_for_user(user):
    return (
        Order.objects.filter(
            models.Q(restaurant__owner=user)
            | models.Q(
                restaurant__staff_for_restaurant__user=user,
                restaurant__staff_for_restaurant__is_active=True,
            )
        )
        .select_related("restaurant")
        .prefetch_related("items_for_order__menu_item")
        .distinct()
    )


class ListCreateOrderAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_queryset(self, user):
        return orders_for_user(user)

    def get(self, request):
        orders = self.get_queryset(request.user)
        serializer = OrderSerializer(orders, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        data = request.data
        # Accept either a single item object or a list of items
        if isinstance(data.get("items"), dict):
            data = {**data, "items": [data["items"]]}

        serializer = OrderSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        restaurant = serializer.validated_data["restaurant"]
        user = request.user

        if not (
            restaurant.owner_id == user.id
            or restaurant.staff_for_restaurant.filter(
                user=user, is_active=True
            ).exists()
        ):
            return Response(
                {"error": "You cannot create an order for this restaurant."},
                status=status.HTTP_403_FORBIDDEN,
            )

        items = serializer.validated_data["items"]

        for item in items:
            if item["menu_item"].category.restaurant_id != restaurant.pk:
                return Response(
                    {
                        "error": (
                            f"Menu item '{item['menu_item'].name}' does not "
                            "belong to this restaurant."
                        )
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        with transaction.atomic():
            order = Order.objects.create(
                restaurant=restaurant,
                order_type=serializer.validated_data.get(
                    "order_type", Order.ORDER_TYPE.DINE_IN
                ),
            )
            Order_Item.objects.bulk_create(
                Order_Item(
                    order=order,
                    menu_item=item["menu_item"],
                    quantity=item["quantity"],
                    subtotal=item["menu_item"].price * item["quantity"],
                )
                for item in items
            )

        order = self.get_queryset(user).get(pk=order.pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)


class OrderStatusUpdateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        order = get_object_or_404(orders_for_user(request.user), pk=pk)

        serializer = OrderStatusUpdateSerializer(
            order, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        order = orders_for_user(request.user).get(pk=pk)
        return Response(OrderSerializer(order).data, status=status.HTTP_200_OK)

