from django.db import models
from django.contrib.auth import get_user_model
from cloudinary.models import CloudinaryField
from django.utils.text import slugify
import uuid
# Create your models here.
User = get_user_model()


class Restaurant(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, primary_key=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="restaurants")
    description = models.TextField(blank=True, default="")
    address = models.CharField(max_length=255, blank=True, default="")
    phone = models.CharField(max_length=32, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    logo = CloudinaryField("/mesero/logo/", blank=True, null=True)
    cover = CloudinaryField("/mesero/cover/", blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or uuid.uuid4().hex[:12]
            slug = base_slug
            # Check if slug already exists in the DB, append a suffix if it does
            while Restaurant.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{uuid.uuid4().hex[:6]}"
            self.slug = slug
        super().save(*args, **kwargs)


    def __str__(self):
        return f"Restaurant- {self.name} for- {self.owner.email}"



class Staff(models.Model):
    class StaffRole(models.TextChoices):
        OWNER = "OWNER", "Owner"
        MANAGER = "MANAGER", "Manager"
        HEAD_CHEF = "HEAD_CHEF", "Head Chef"
        LINE_COOK = "LINE_COOK", "Line Cook"
        WAITER = "WAITER", "Waiter / Server"
        CASHIER = "CASHIER", "Cashier"
        BARTENDER = "BARTENDER", "Bartender"
        DELIVERY = "DELIVERY", "Delivery Driver"
        KITCHEN_ASSISTANT = "KITCHEN_ASSISTANT", "Kitchen Assistant"


    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=StaffRole.choices, default=StaffRole.HEAD_CHEF)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="staff_for_restaurant")
    is_active = models.BooleanField(default=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "restaurant"],
                name="unique-constraint-for-staff"
            
                )
                        ]

    def __str__(self):
        return f"Staff for Restaurant - {self.restaurant.name}"


class Categories(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="menu_categories")
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=225)
    is_active = models.BooleanField(default=True)



    def save(self, *args, **kwargs):
        if not self.slug:
            slug = slugify(self.name)
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Category {self.name} for - {self.restaurant.name}"



class MenuItem(models.Model):
    name = models.CharField(max_length=200)
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, related_name="menu_item")
    image = CloudinaryField("mesero/menu_item/", blank=True, null=True)
    price = models.DecimalField(max_digits=10, 
        decimal_places=2,
        default=0.00)
    is_available = models.BooleanField(default=True)
    description = models.TextField()

    def __str__(self):
        return f"Menu Item {self.name} for Restaurant {self.category.restaurant.name} - Category {self.category.name} "





class Inventory(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name="restaurant_inventory")
    name = models.CharField(max_length=200)
    slug = models.CharField(max_length=225)
    is_active = models.BooleanField(default=True)



    def save(self, *args, **kwargs):
        if not self.slug:
            slug = slugify(self.name)
            self.slug = slug

        super().save(*args, **kwargs)

    def __str__(self):
        return f"Inventory for - {self.restaurant.name}"



class InventoryItem(models.Model):
    name = models.CharField(max_length=200)
    inventory = models.ForeignKey(Inventory, on_delete=models.CASCADE, related_name="inventory_item")
    image = CloudinaryField("mesero/inventory_item/", blank=True, null=True)
    quantity = models.PositiveSmallIntegerField()
    unit_measurement = models.CharField(max_length=100)
    low_stock_threshold = models.PositiveSmallIntegerField(default=10)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return f"Inventory Item - {self.name}"



