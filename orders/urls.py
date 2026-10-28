from django.urls import path
from .views import ListCreateOrderAPIView, OrderStatusUpdateAPIView

urlpatterns =[
    path("orders/", ListCreateOrderAPIView.as_view()),
    path("orders/<int:pk>/", OrderStatusUpdateAPIView.as_view()),
]