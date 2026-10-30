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


class StaffUserSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "name"]

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip() or obj.email.split("@")[0]


class StaffSerializer(serializers.ModelSerializer):
    user = StaffUserSerializer(read_only=True)
    joined_at = serializers.DateTimeField(source="user.date_joined", read_only=True)

    class Meta:
        model = Staff
        fields = ["id", "user", "role", "restaurant", "is_active", "joined_at"]
        read_only_fields = ["id", "user", "restaurant", "joined_at"]


class StaffInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
    role = serializers.ChoiceField(choices=Staff.StaffRole.choices)

    def validate_role(self, value):
        if value == Staff.StaffRole.OWNER:
            raise serializers.ValidationError("The owner role cannot be assigned.")
        return value


class StaffUpdateSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=Staff.StaffRole.choices, required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_role(self, value):
        if value == Staff.StaffRole.OWNER:
            raise serializers.ValidationError("The owner role cannot be assigned.")
        return value


class MenuItemSerializer(serializers.ModelSerializer):
    category = serializers.PrimaryKeyRelatedField(queryset=Categories.objects.all())
    category_name = serializers.CharField(source="category.name", read_only=True)
    image = CloudinaryImageField(required=False, allow_null=True)

    class Meta:
        model = MenuItem
        fields = ["id", "name", "category", "category_name", "image", "price", "is_available", "description"]

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


class StockAdjustmentSerializer(serializers.Serializer):
    delta = serializers.IntegerField()

    def validate_delta(self, value):
        if value == 0:
            raise serializers.ValidationError("Adjustment cannot be zero.")
        return value


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