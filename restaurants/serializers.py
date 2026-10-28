from restaurants.models import Staff
from rest_framework import serializers
from .models import Restaurant, Categories, MenuItem, Inventory, InventoryItem
from django.contrib.auth import get_user_model
from users.serializers import UserSerializer

User = get_user_model()


class CloudinaryImageField(serializers.ImageField):
    def to_representation(self, value):
        if not value:
            return None
        return value.url


class RestaurantSerializer(serializers.ModelSerializer):
    logo = CloudinaryImageField(required=False, allow_null=True)
    cover = CloudinaryImageField(required=False, allow_null=True)

    class Meta:
        model = Restaurant
        fields = [
            "owner",
            "name",
            "slug",
            "description",
            "address",
            "phone",
            "email",
            "logo",
            "cover",
        ]
        read_only_fields = ["owner", "slug"]


class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Staff
        fields = ["user", "role", "restaurant", "is_active"]


class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Categories.objects.all())
    image = CloudinaryImageField(required=False, allow_null=True)

    class Meta:
        model = MenuItem
        fields = ["id", "name", "category", "image", "price", "is_available", "description"]

class CategorySerializer(serializers.ModelSerializer):
    restaurant = serializers.PrimaryKeyRelatedField(read_only=True)
    menu_item = MenuItemSerializer(many=True, read_only=True)

    class Meta:
        model = Categories
        fields = ["id", "restaurant", "name", "slug", "is_active", "menu_item"]
        extra_kwargs = {"slug": {"read_only": True}}




class InventoryItemSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()
    inventory = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            "id",
            "name",
            "inventory",
            "image",
            "quantity",
            "unit_measurement",
            "low_stock_threshold",
            "is_available",
        ]

    def get_image(self, obj):
        if obj.image:
            return obj.image.url
        return None


class InventorySerializer(serializers.ModelSerializer):
    restaurant = serializers.PrimaryKeyRelatedField(read_only=True)
    inventory_item = InventoryItemSerializer(many=True, read_only=True)

    class Meta:
        model = Inventory
        fields = ["id", "restaurant", "name", "slug", "is_active", "inventory_item"]
        extra_kwargs = {"slug": {"read_only": True}}



class RestaurantDetailSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    logo = CloudinaryImageField(required=False, allow_null=True)
    cover = CloudinaryImageField(required=False, allow_null=True)
    restaurant_inventory = InventorySerializer(many=True, read_only=True)
    menu_categories = CategorySerializer(many=True, read_only=True)
    staff_for_restaurant = StaffSerializer(many=True, read_only=True)
    staff_count = serializers.SerializerMethodField()
    menu_categories_count = serializers.SerializerMethodField()

    class Meta:
        model = Restaurant
        fields = [
            "owner",
            "name",
            "slug",
            "description",
            "address",
            "phone",
            "email",
            "logo",
            "cover",
            "restaurant_inventory",
            "menu_categories",
            "staff_for_restaurant",
            "staff_count",
            "menu_categories_count",
        ]
        read_only_fields = ["owner", "slug"]

    def get_staff_count(self, obj):
        return obj.staff_for_restaurant.count()

    def get_menu_categories_count(self, obj):
        return obj.menu_categories.count()