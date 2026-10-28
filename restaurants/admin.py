from django.contrib import admin
from .models import Restaurant, MenuItem, InventoryItem, Categories, Inventory, Staff

# Register your models here.

@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("slug", "name", "owner")
    list_display_links = ("slug", "name")
    search_fields = ("slug", "name", "owner__email")
    list_filter = ("owner",)



admin.site.register(Staff)

admin.site.register(Inventory)

admin.site.register(InventoryItem)

admin.site.register(Categories)

admin.site.register(MenuItem)


