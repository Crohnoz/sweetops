from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html

from .models import Order, OrderItem, SectorTicket


def money(value):
    return f"${value:,.0f}".replace(",", ".")


def render_badge(label, bg, color):
    return format_html(
        '''
        <span style="
            background:{};
            color:{};
            padding:6px 12px;
            border-radius:999px;
            font-weight:bold;
            font-size:12px;
            display:inline-block;
            white-space:nowrap;
        ">
            {}
        </span>
        ''',
        bg,
        color,
        label,
    )


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ("product",)

    readonly_fields = (
        "subtotal",
        "sector_snapshot",
        "created_at",
    )

    fields = (
        "product",
        "quantity",
        "unit_price",
        "subtotal",
        "sector_snapshot",
        "created_at",
    )


class SectorTicketInline(admin.TabularInline):
    model = SectorTicket
    extra = 0
    can_delete = False

    readonly_fields = (
        "sector",
        "status",
        "printed",
        "created_at",
        "updated_at",
        "ready_at",
        "delivered_at",
        "preparation_minutes",
        "delivery_minutes",
    )

    fields = (
        "sector",
        "status",
        "printed",
        "created_at",
        "updated_at",
        "ready_at",
        "delivered_at",
        "preparation_minutes",
        "delivery_minutes",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "customer_name",
        "status_badge",
        "formatted_total",
        "items_count",
        "total_units_display",
        "tickets_count",
        "duration_badge",
        "created_at",
        "completed_at",
    )

    list_filter = (
        "status",
        "created_at",
        "completed_at",
    )

    search_fields = (
        "id",
        "customer_name",
        "notes",
        "items__product__name",
    )

    readonly_fields = (
        "total",
        "items_count",
        "total_units_display",
        "duration_badge",
        "created_at",
        "updated_at",
        "completed_at",
    )

    ordering = (
        "-created_at",
    )

    inlines = [
        OrderItemInline,
        SectorTicketInline,
    ]

    fieldsets = (
        (
            "Información pedido",
            {
                "fields": (
                    "customer_name",
                    "status",
                    "notes",
                    "total",
                    "items_count",
                    "total_units_display",
                    "duration_badge",
                )
            },
        ),
        (
            "Timestamps",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                    "completed_at",
                )
            },
        ),
    )

    actions = (
        "mark_in_progress",
        "mark_completed",
        "mark_cancelled",
        "recalculate_totals",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .prefetch_related("items", "sector_tickets")
        )

    def formatted_total(self, obj):
        return money(obj.total)

    formatted_total.short_description = "Total"
    formatted_total.admin_order_field = "total"

    def items_count(self, obj):
        return obj.items.count()

    items_count.short_description = "Items"

    def total_units_display(self, obj):
        return obj.total_units

    total_units_display.short_description = "Unidades"

    def tickets_count(self, obj):
        return obj.sector_tickets.count()

    tickets_count.short_description = "Comandas"

    def duration_badge(self, obj):
        minutes = obj.duration_minutes

        if minutes is None:
            return "-"

        if minutes <= 10:
            return render_badge(f"{minutes} min", "#14532d", "#bbf7d0")

        if minutes <= 20:
            return render_badge(f"{minutes} min", "#854d0e", "#fde68a")

        return render_badge(f"{minutes} min", "#7f1d1d", "#fecaca")

    duration_badge.short_description = "Duración"

    def status_badge(self, obj):
        colors = {
            "pending": ("#854d0e", "#fde68a"),
            "in_progress": ("#1d4ed8", "#bfdbfe"),
            "completed": ("#14532d", "#bbf7d0"),
            "cancelled": ("#7f1d1d", "#fecaca"),
        }

        bg, text = colors.get(obj.status, ("#334155", "white"))

        return render_badge(
            obj.get_status_display(),
            bg,
            text,
        )

    status_badge.short_description = "Estado"

    @admin.action(description="Marcar pedidos en preparación")
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(
            status="in_progress",
            completed_at=None,
        )

        self.message_user(
            request,
            f"{updated} pedidos marcados en preparación.",
        )

    @admin.action(description="Marcar pedidos como completados")
    def mark_completed(self, request, queryset):
        updated = queryset.update(
            status="completed",
            completed_at=timezone.now(),
        )

        self.message_user(
            request,
            f"{updated} pedidos completados.",
        )

    @admin.action(description="Cancelar pedidos")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(
            status="cancelled",
            completed_at=timezone.now(),
        )

        self.message_user(
            request,
            f"{updated} pedidos cancelados.",
        )

    @admin.action(description="Recalcular totales")
    def recalculate_totals(self, request, queryset):
        count = 0

        for order in queryset:
            order.calculate_total()
            count += 1

        self.message_user(
            request,
            f"{count} pedidos recalculados.",
        )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "formatted_unit_price",
        "formatted_subtotal",
        "sector_snapshot",
        "created_at",
    )

    list_filter = (
        "sector_snapshot",
        "created_at",
    )

    search_fields = (
        "product__name",
        "order__customer_name",
        "order__id",
    )

    autocomplete_fields = (
        "order",
        "product",
    )

    readonly_fields = (
        "subtotal",
        "sector_snapshot",
        "created_at",
    )

    ordering = (
        "-created_at",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("order", "product")
        )

    def formatted_unit_price(self, obj):
        return money(obj.unit_price)

    formatted_unit_price.short_description = "Precio"

    def formatted_subtotal(self, obj):
        return money(obj.subtotal)

    formatted_subtotal.short_description = "Subtotal"


@admin.register(SectorTicket)
class SectorTicketAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "sector_badge",
        "status_badge",
        "preparation_badge",
        "delivery_badge",
        "printed",
        "created_at",
        "ready_at",
        "delivered_at",
    )

    list_filter = (
        "sector",
        "status",
        "printed",
        "created_at",
    )

    search_fields = (
        "order__customer_name",
        "order__id",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
        "ready_at",
        "delivered_at",
        "preparation_badge",
        "delivery_badge",
    )

    ordering = (
        "-created_at",
    )

    actions = (
        "mark_pending",
        "mark_in_progress",
        "mark_ready",
        "mark_delivered",
        "mark_cancelled",
        "mark_printed",
        "mark_unprinted",
    )

    def get_queryset(self, request):
        return (
            super()
            .get_queryset(request)
            .select_related("order")
        )

    def sector_badge(self, obj):
        colors = {
            "cafeteria": ("#92400e", "#fde68a"),
            "display": ("#1d4ed8", "#dbeafe"),
            "kitchen": ("#14532d", "#bbf7d0"),
        }

        bg, text = colors.get(obj.sector, ("#334155", "white"))

        return render_badge(
            obj.sector.upper(),
            bg,
            text,
        )

    sector_badge.short_description = "Sector"

    def status_badge(self, obj):
        colors = {
            "pending": ("#854d0e", "#fde68a"),
            "in_progress": ("#1d4ed8", "#bfdbfe"),
            "ready": ("#14532d", "#bbf7d0"),
            "delivered": ("#166534", "#dcfce7"),
            "cancelled": ("#7f1d1d", "#fecaca"),
        }

        bg, text = colors.get(obj.status, ("#334155", "white"))

        return render_badge(
            obj.get_status_display(),
            bg,
            text,
        )

    status_badge.short_description = "Estado"

    def preparation_badge(self, obj):
        minutes = obj.preparation_minutes

        if minutes is None:
            return "-"

        if minutes <= 5:
            return render_badge(f"{minutes} min", "#14532d", "#bbf7d0")

        if minutes <= 15:
            return render_badge(f"{minutes} min", "#854d0e", "#fde68a")

        return render_badge(f"{minutes} min", "#7f1d1d", "#fecaca")

    preparation_badge.short_description = "Prep"

    def delivery_badge(self, obj):
        minutes = obj.delivery_minutes

        if minutes is None:
            return "-"

        return render_badge(
            f"{minutes} min",
            "#1d4ed8",
            "#dbeafe",
        )

    delivery_badge.short_description = "Entrega"

    @admin.action(description="Marcar comandas como pendientes")
    def mark_pending(self, request, queryset):
        updated = queryset.update(
            status="pending",
            ready_at=None,
            delivered_at=None,
        )

        self.message_user(
            request,
            f"{updated} comandas marcadas como pendientes.",
        )

    @admin.action(description="Marcar comandas en preparación")
    def mark_in_progress(self, request, queryset):
        updated = queryset.update(
            status="in_progress",
        )

        self.message_user(
            request,
            f"{updated} comandas marcadas en preparación.",
        )

    @admin.action(description="Marcar comandas como listas")
    def mark_ready(self, request, queryset):
        now = timezone.now()

        updated = queryset.update(
            status="ready",
            ready_at=now,
        )

        self.message_user(
            request,
            f"{updated} comandas listas.",
        )

    @admin.action(description="Marcar comandas como entregadas")
    def mark_delivered(self, request, queryset):
        now = timezone.now()

        updated = queryset.update(
            status="delivered",
            ready_at=now,
            delivered_at=now,
        )

        for ticket in queryset:
            ticket.order.refresh_status_from_tickets()

        self.message_user(
            request,
            f"{updated} comandas entregadas.",
        )

    @admin.action(description="Cancelar comandas")
    def mark_cancelled(self, request, queryset):
        updated = queryset.update(
            status="cancelled",
        )

        for ticket in queryset:
            ticket.order.refresh_status_from_tickets()

        self.message_user(
            request,
            f"{updated} comandas canceladas.",
        )

    @admin.action(description="Marcar como impreso")
    def mark_printed(self, request, queryset):
        updated = queryset.update(
            printed=True,
        )

        self.message_user(
            request,
            f"{updated} comandas marcadas como impresas.",
        )

    @admin.action(description="Marcar como no impreso")
    def mark_unprinted(self, request, queryset):
        updated = queryset.update(
            printed=False,
        )

        self.message_user(
            request,
            f"{updated} comandas marcadas como no impresas.",
        )