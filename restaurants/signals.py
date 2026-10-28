from django.dispatch import receiver
from django.db.models.signals import post_save
from .models import InventoryItem, Restaurant, Staff


@receiver(post_save, sender=Restaurant)
def add_restaurant_owner_as_staff(sender, instance, created, *args, **kwargs):
    if created:
        Staff.objects.create(
            user=instance.owner,
            role="OWNER",
            restaurant=instance
        )



@receiver(post_save, sender=InventoryItem)
def send_low_stock_email_notification(sender, instance, created, *args, **kwargs):
    if not created: 
        if instance.quantity <= instance.low_stock_threshold:
            # send_email()
            print(f"Your Inventory item - {instance.name}, has less than {instance.low_stock_threshold} items in stock. ")


@receiver(post_save, sender=InventoryItem)
def send_stock_finished_email_notification(sender, instance, created, *args, **kwargs):
    if not created: 
        if instance.quantity == 0:
            # send_email()
            print(f"You are out of Inventory item - {instance.name}")
        