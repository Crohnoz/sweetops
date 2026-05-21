from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'customer_name',
        'payment_method',
        'status',
        'total',
        'created_at',
    )

    list_filter = (
        'payment_method',
        'status',
        'created_at',
    )

    search_fields = (
        'customer_name',
    )

    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):

    list_display = (
        'order',
        'product',
        'quantity',
        'unit_price',
        'subtotal',
    )