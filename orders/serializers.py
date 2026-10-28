from rest_framework import serializers
from restaurants.models import MenuItem
from .models import Order_Item, Order


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order_Item
        fields = ["id", "menu_item", "quantity", "subtotal"]
        read_only_fields = ["subtotal"]


class OrderItemInputSerializer(serializers.Serializer):
    menu_item = serializers.PrimaryKeyRelatedField(
        queryset=MenuItem.objects.all(), required=False
    )
    id = serializers.IntegerField(required=False, write_only=True)
    quantity = serializers.IntegerField(min_value=1)

    def validate(self, attrs):
        menu_item = attrs.get("menu_item")

        if menu_item is None:
            item_id = attrs.get("id")
            if item_id is None:
                raise serializers.ValidationError(
                    {"menu_item": "This field is required."}
                )
            menu_item = MenuItem.objects.filter(pk=item_id).first()
            if menu_item is None:
                raise serializers.ValidationError(
                    {"id": "Menu item does not exist."}
                )

        attrs["menu_item"] = menu_item
        attrs.pop("id", None)
        return attrs


class OrderSerializer(serializers.ModelSerializer):
    items_for_order = OrderItemSerializer(many=True, read_only=True)
    items = OrderItemInputSerializer(many=True, write_only=True, allow_empty=False)

    class Meta:
        model = Order
        fields = [
            "id",
            "restaurant",
            "order_reference",
            "order_type",
            "status",
            "items_for_order",
            "items",
        ]
        extra_kwargs = {
            "order_reference": {"read_only": True},
            "status": {"read_only": True},
        }


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ["status"]

