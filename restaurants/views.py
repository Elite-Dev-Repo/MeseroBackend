from django.contrib.auth import get_user_model
from restaurants.serializers import (
    StaffInviteSerializer,
    StaffSerializer,
    StaffUpdateSerializer,
)
from restaurants.models import Staff
from restaurants.permissions import IsOwnerOrStaffOnly
from restaurants.serializers import RestaurantDetailSerializer
from rest_framework.response import Response
from django.shortcuts import get_object_or_404, render
from .serializers import RestaurantSerializer, MenuItemSerializer, InventoryItemSerializer, CategorySerializer, InventorySerializer, StockAdjustmentSerializer
from .models import Restaurant, MenuItem, InventoryItem, Categories, Inventory
from django.db import models
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.views import APIView

User = get_user_model()


def get_user_restaurant(user, slug):
    return Restaurant.objects.filter(
        models.Q(slug=slug, owner=user)
        | models.Q(
            slug=slug,
            staff_for_restaurant__user=user,
            staff_for_restaurant__is_active=True,
        )
    ).distinct().first()


# Create your views here.


class CreateRestaurantView(generics.CreateAPIView):
    queryset = Restaurant.objects.select_related("owner")
    serializer_class = RestaurantDetailSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [FormParser, MultiPartParser]


    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)




class RestaurantRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RestaurantDetailSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOnly]
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    lookup_field = "slug"

    def get_queryset(self):
        user = self.request.user
        return Restaurant.objects.filter(
            models.Q(owner=user) | models.Q(staff_for_restaurant__user=user, staff_for_restaurant__is_active=True)
        ).prefetch_related("restaurant_inventory", "menu_categories", "staff_for_restaurant").distinct()


    def update(self, request, *args, **kwargs):
        restaurant = self.get_object()

        if request.user != restaurant.owner:
            raise PermissionDenied("you are not permitted to perform this action")

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        restaurant = self.get_object()

        if request.user != restaurant.owner:
            raise PermissionDenied("you are not permitted to perform this action")

        return super().destroy(request, *args, **kwargs)

class CategoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOnly]
    lookup_field = "slug"

    def get_restaurant(self):
        user = self.request.user
        restaurant_slug = (
            self.kwargs.get("restaurant_slug")
            or self.request.data.get("restaurant_slug")
        )

        if not restaurant_slug:
            raise ValidationError({"restaurant_slug": "This field is required."})

        restaurant = Restaurant.objects.filter(
            models.Q(slug=restaurant_slug, owner=user)
            | models.Q(
                slug=restaurant_slug,
                staff_for_restaurant__user=user,
                staff_for_restaurant__is_active=True,
            )
        ).distinct().first()

        if not restaurant:
            raise PermissionDenied(
                "You cannot add a category to this restaurant."
            )

        return restaurant

    def get_queryset(self):
        user = self.request.user
        
        # Check query params (for GET) first, then request.data (for POST)
        restaurant_slug = (
            self.kwargs.get("restaurant_slug") or 
            self.request.data.get("restaurant_slug")
        )
        
        if not restaurant_slug:
            return Categories.objects.none() 
            

        # Filter categories by restaurant and ensure user has owner/staff access, plus prefetch optimization
        return Categories.objects.filter(
            models.Q(restaurant__slug=restaurant_slug, restaurant__owner=user) |
            models.Q(restaurant__slug=restaurant_slug, restaurant__staff_for_restaurant__user=user, restaurant__staff_for_restaurant__is_active=True)
        ).prefetch_related("menu_item").distinct()

    def perform_create(self, serializer):
        serializer.save(restaurant=self.get_restaurant())


class MenuItemListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOnly]

    def get_queryset(self):
        user = self.request.user
        queryset = MenuItem.objects.filter(
            models.Q(category__restaurant__owner=user) | 
            models.Q(category__restaurant__staff_for_restaurant__user=user, category__restaurant__staff_for_restaurant__is_active=True)
        ).select_related("category").distinct()

        restaurant = self.request.query_params.get("restaurant")
        if restaurant:
            queryset = queryset.filter(category__restaurant__slug=restaurant)

        category = self.request.query_params.get("category")
        if category and category.isdigit():
            queryset = queryset.filter(category_id=category)

        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                models.Q(name__icontains=search)
                | models.Q(description__icontains=search)
            )

        return queryset

    def perform_create(self, serializer):
        category = serializer.validated_data["category"]
        restaurant = category.restaurant
        user = self.request.user
        if not (restaurant.owner == user or restaurant.staff_for_restaurant.filter(user=user, is_active=True).exists()):
            raise PermissionDenied("You can only add items to your own restaurant's categories.")
        serializer.save()


class CategoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Categories.objects.filter(
            models.Q(restaurant__owner=user)
            | models.Q(
                restaurant__staff_for_restaurant__user=user,
                restaurant__staff_for_restaurant__is_active=True,
            )
        ).distinct()


class MenuItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MenuItemSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def get_queryset(self):
        user = self.request.user
        return MenuItem.objects.filter(
            models.Q(category__restaurant__owner=user)
            | models.Q(
                category__restaurant__staff_for_restaurant__user=user,
                category__restaurant__staff_for_restaurant__is_active=True,
            )
        ).distinct()

    def perform_update(self, serializer):
        category = serializer.validated_data.get("category", serializer.instance.category)
        restaurant = category.restaurant
        user = self.request.user
        if not (
            restaurant.owner == user
            or restaurant.staff_for_restaurant.filter(user=user, is_active=True).exists()
        ):
            raise PermissionDenied(
                "You can only move items to your own restaurant's categories."
            )
        serializer.save()




class InventoryListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_restaurant(self):
        restaurant = get_user_restaurant(
            self.request.user, self.kwargs.get("restaurant_slug")
        )
        if not restaurant:
            raise PermissionDenied("You cannot manage inventory for this restaurant.")
        return restaurant

    def get_queryset(self):
        return Inventory.objects.filter(
            restaurant=self.get_restaurant()
        ).prefetch_related("inventory_item")

    def perform_create(self, serializer):
        serializer.save(restaurant=self.get_restaurant())


class InventoryDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Inventory.objects.filter(
            models.Q(restaurant__owner=user)
            | models.Q(
                restaurant__staff_for_restaurant__user=user,
                restaurant__staff_for_restaurant__is_active=True,
            )
        ).distinct()


class InventoryItemListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_restaurant(self):
        restaurant = get_user_restaurant(
            self.request.user, self.kwargs.get("restaurant_slug")
        )
        if not restaurant:
            raise PermissionDenied("You cannot manage inventory for this restaurant.")
        return restaurant

    def get_queryset(self):
        return InventoryItem.objects.filter(
            inventory__restaurant=self.get_restaurant()
        ).select_related("inventory")

    def perform_create(self, serializer):
        restaurant = self.get_restaurant()
        inventory = Inventory.objects.filter(restaurant=restaurant).first()
        if not inventory:
            inventory = Inventory.objects.create(
                restaurant=restaurant, name="Main Inventory"
            )
        serializer.save(inventory=inventory)


class InventoryItemDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = InventoryItemSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return InventoryItem.objects.filter(
            models.Q(inventory__restaurant__owner=user)
            | models.Q(
                inventory__restaurant__staff_for_restaurant__user=user,
                inventory__restaurant__staff_for_restaurant__is_active=True,
            )
        ).distinct()


class InventoryItemAdjustAPIView(generics.GenericAPIView):
    serializer_class = StockAdjustmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return InventoryItem.objects.filter(
            models.Q(inventory__restaurant__owner=user)
            | models.Q(
                inventory__restaurant__staff_for_restaurant__user=user,
                inventory__restaurant__staff_for_restaurant__is_active=True,
            )
        ).distinct()

    def post(self, request, pk):
        item = get_object_or_404(self.get_queryset(), pk=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_quantity = item.quantity + serializer.validated_data["delta"]
        if new_quantity < 0:
            raise ValidationError({"delta": "Stock cannot go below zero."})
        item.quantity = new_quantity
        item.save(update_fields=["quantity"])
        return Response(
            InventoryItemSerializer(item).data, status=status.HTTP_200_OK
        )


class StaffListAPIView(generics.ListAPIView):
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOnly]

    def get_queryset(self):
        restaurant = get_user_restaurant(
            self.request.user, self.kwargs.get("restaurant_slug")
        )
        if not restaurant:
            raise PermissionDenied("You cannot view staff for this restaurant.")
        return Staff.objects.filter(restaurant=restaurant).select_related(
            "user", "restaurant"
        )


class StaffInviteAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, restaurant_slug):
        restaurant = get_user_restaurant(request.user, restaurant_slug)
        if not restaurant:
            raise PermissionDenied("You cannot manage staff for this restaurant.")
        if restaurant.owner != request.user:
            raise PermissionDenied("Only the restaurant owner can invite staff.")

        serializer = StaffInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response(
                {"email": "No account found with that email address."},
                status=status.HTTP_404_NOT_FOUND,
            )
        if Staff.objects.filter(user=user, restaurant=restaurant).exists():
            return Response(
                {"email": "This user is already a staff member."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        staff = Staff.objects.create(
            user=user,
            restaurant=restaurant,
            role=serializer.validated_data["role"],
            is_active=True,
        )
        return Response(StaffSerializer(staff).data, status=status.HTTP_201_CREATED)


class StaffDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_staff(self, request, restaurant_slug, pk):
        restaurant = get_user_restaurant(request.user, restaurant_slug)
        if not restaurant:
            raise PermissionDenied("You cannot manage staff for this restaurant.")
        if restaurant.owner != request.user:
            raise PermissionDenied("Only the restaurant owner can manage staff.")
        staff = get_object_or_404(
            Staff.objects.select_related("user", "restaurant"),
            pk=pk,
            restaurant=restaurant,
        )
        if staff.role == Staff.StaffRole.OWNER:
            raise PermissionDenied("The owner's staff record cannot be changed.")
        return staff

    def patch(self, request, restaurant_slug, pk):
        staff = self.get_staff(request, restaurant_slug, pk)
        serializer = StaffUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        for field, value in serializer.validated_data.items():
            setattr(staff, field, value)
        staff.save(update_fields=list(serializer.validated_data.keys()))
        return Response(StaffSerializer(staff).data, status=status.HTTP_200_OK)

    def delete(self, request, restaurant_slug, pk):
        staff = self.get_staff(request, restaurant_slug, pk)
        staff.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)