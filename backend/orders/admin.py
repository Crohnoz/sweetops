from django.contrib import admin
from .models import Order, OrderItem, SectorTicket


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ("subtotal", "sector_snapshot")


class SectorTicketInline(admin.TabularInline):
    model = SectorTicket
    extra = 0
    readonly_fields = ("sector", "created_at")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer_name", "status", "total", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("customer_name",)
    inlines = [OrderItemInline, SectorTicketInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "unit_price",
        "subtotal",
        "sector_snapshot",
    )

    readonly_fields = (
        "subtotal",
        "sector_snapshot",
    )


@admin.register(SectorTicket)
class SectorTicketAdmin(admin.ModelAdmin):
    list_display = ("order", "sector", "status", "printed", "created_at")
    list_filter = ("sector", "status", "printed")