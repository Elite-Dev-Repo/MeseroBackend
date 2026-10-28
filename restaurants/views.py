from restaurants.serializers import StaffSerializer
from restaurants.models import Staff
from restaurants.permissions import IsOwnerOrStaffOnly
from restaurants.serializers import RestaurantDetailSerializer
from rest_framework.response import Response
from django.shortcuts import render
from .serializers import RestaurantSerializer, MenuItemSerializer, InventoryItemSerializer, CategorySerializer, InventorySerializer
from .models import Restaurant, MenuItem, InventoryItem, Categories, Inventory
from django.db import models
from rest_framework import generics
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.exceptions import PermissionDenied, ValidationError


# Create your views here.


class CreateRestaurantView(generics.CreateAPIView):
    queryset = Restaurant.objects.select_related("owner")
    serializer_class = RestaurantSerializer
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
        return MenuItem.objects.filter(
            models.Q(category__restaurant__owner=user) | 
            models.Q(category__restaurant__staff_for_restaurant__user=user, category__restaurant__staff_for_restaurant__is_active=True)
        ).distinct()

    def perform_create(self, serializer):
        category = serializer.validated_data["category"]
        restaurant = category.restaurant
        user = self.request.user
        if not (restaurant.owner == user or restaurant.staff_for_restaurant.filter(user=user, is_active=True).exists()):
            raise PermissionDenied("You can only add items to your own restaurant's categories.")
        serializer.save()




class inventoryListCreateAPIView(generics.ListCreateAPIView):
    queryset = Inventory.objects.select_related("menu_items").all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]
    lookup_field = "slug"


class StaffListAPIView(generics.ListAPIView):
    serializer_class = StaffSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrStaffOnly]

    def get_queryset(self):
        restaurant_slug = self.kwargs.get("restaurant_slug")
        restaurant = Restaurant.objects.get(slug=restaurant_slug)
        return Staff.objects.filter(restaurant=restaurant).select_related("user", "restaurant").all()