from restaurants.views import StaffListAPIView
from django.urls import path
from .views import CreateRestaurantView,RestaurantRetrieveUpdateDestroyView,MenuItemListCreateAPIView,CategoryListCreateAPIView, CategoryDetailAPIView, MenuItemDetailAPIView



urlpatterns = [
    path("restaurant/create/", CreateRestaurantView.as_view()),
     path("restaurant/<str:slug>/", RestaurantRetrieveUpdateDestroyView.as_view()),
     path("staffs/<str:restaurant_slug>", StaffListAPIView.as_view()),
     path("<str:restaurant_slug>/category/", CategoryListCreateAPIView.as_view()),
     path("category/<int:pk>/", CategoryDetailAPIView.as_view()),
     path("menu_items/", MenuItemListCreateAPIView.as_view()),
     path("menu_items/<int:pk>/", MenuItemDetailAPIView.as_view())

]