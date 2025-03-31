from django.contrib import admin
from orders.models import Order, Item, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    inlines = [OrderItemInline, ]

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    pass

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    pass