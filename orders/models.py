from django.db import models
from users.models import User
from restaurants.models import MenuItem, Restaurant
import secrets

# Create your models here.


class Order(models.Model):
    class ORDER_TYPE(models.TextChoices):
        DINE_IN = "DINE IN"
        DELIVERY = "DELIVERY"
        TAKE_AWAY = "TAKE AWAY"
    class ORDER_STATUS(models.TextChoices):
        PENDING = "PENDING"
        PREPARING = "PREPARING"
        DELIVERED = "DELIVERED"
        CANCELLED = "CANCELLED"

    order_reference = models.CharField(max_length=100)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="restaurant_orders")
    order_type = models.CharField(choices=ORDER_TYPE.choices, default=ORDER_TYPE.DINE_IN)
    status = models.CharField(choices=ORDER_STATUS.choices, default=ORDER_STATUS.PENDING)

    def generate_ref(self):
        rand_digits = secrets.token_hex(3).upper()
        self.order_reference = f"ORD-{rand_digits}"
    
    def save(self, *args, **kwargs):
        if not self.order_reference:
            self.generate_ref()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.order_reference} - for restaurant - {self.restaurant.name}"




class Order_Item(models.Model):
    menu_item = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, related_name="order_item", null=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items_for_order")
    quantity = models.PositiveSmallIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=10, 
        decimal_places=2,
        default=0.00)


    def __str__(self):
        return f"order item for Order {self.order.order_reference}"