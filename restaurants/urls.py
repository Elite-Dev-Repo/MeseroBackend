from restaurants.views import (
    StaffDetailAPIView,
    StaffInviteAPIView,
    StaffListAPIView,
)
from django.urls import path
from .views import CreateRestaurantView,RestaurantRetrieveUpdateDestroyView,MenuItemListCreateAPIView,CategoryListCreateAPIView, CategoryDetailAPIView, MenuItemDetailAPIView, InventoryListCreateAPIView, InventoryDetailAPIView, InventoryItemListCreateAPIView, InventoryItemDetailAPIView, InventoryItemAdjustAPIView



urlpatterns = [
    path("restaurant/create/", CreateRestaurantView.as_view()),
     path("restaurant/<str:slug>/", RestaurantRetrieveUpdateDestroyView.as_view()),
     path("staffs/<str:restaurant_slug>/", StaffListAPIView.as_view()),
     path("staffs/<str:restaurant_slug>/invite/", StaffInviteAPIView.as_view()),
     path("staffs/<str:restaurant_slug>/<int:pk>/", StaffDetailAPIView.as_view()),
     path("<str:restaurant_slug>/category/", CategoryListCreateAPIView.as_view()),
     path("category/<int:pk>/", CategoryDetailAPIView.as_view()),
     path("menu_items/", MenuItemListCreateAPIView.as_view()),
     path("menu_items/<int:pk>/", MenuItemDetailAPIView.as_view()),
     path("<str:restaurant_slug>/inventory/", InventoryListCreateAPIView.as_view()),
     path("inventory/<int:pk>/", InventoryDetailAPIView.as_view()),
     path("<str:restaurant_slug>/inventory/items/", InventoryItemListCreateAPIView.as_view()),
     path("inventory/items/<int:pk>/", InventoryItemDetailAPIView.as_view()),
     path("inventory/items/<int:pk>/adjust/", InventoryItemAdjustAPIView.as_view()),

]