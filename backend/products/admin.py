from django.contrib import admin
from django.utils.html import format_html

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        "thumbnail",
        "name",
        "category",
        "sector",
        "formatted_price",
        "stock",
        "minimum_stock",
        "stock_status",
        "availability_badge",
        "olaclick_id",
        "updated_at",
    )

    list_filter = (
        "is_available",
        "category",
        "sector",
        "updated_at",
    )

    search_fields = (
        "name",
        "category",
        "sector",
        "olaclick_id",
    )

    readonly_fields = (
        "image_preview",
        "created_at",
        "updated_at",
    )

    list_editable = (
        "stock",
        "minimum_stock",
    )

    ordering = (
        "-is_available",
        "category",
        "name",
    )

    actions = (
        "mark_as_available",
        "mark_as_unavailable",
    )

    fieldsets = (
        (
            "Información principal",
            {
                "fields": (
                    "name",
                    "category",
                    "sector",
                    "description",
                    "price",
                    "is_available",
                )
            },
        ),
        (
            "Inventario",
            {
                "fields": (
                    "stock",
                    "minimum_stock",
                )
            },
        ),
        (
            "Imagen / OlaClick",
            {
                "fields": (
                    "image_url",
                    "image_preview",
                    "olaclick_id",
                )
            },
        ),
        (
            "Auditoría",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )

    def formatted_price(self, obj):
        return f"${obj.price:,.0f}".replace(",", ".")

    formatted_price.short_description = "Precio"
    formatted_price.admin_order_field = "price"

    def thumbnail(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="width:52px;height:52px;object-fit:cover;border-radius:10px;" />',
                obj.image_url,
            )

        return format_html(
            '<div style="width:52px;height:52px;border-radius:10px;background:#1f2937;display:flex;align-items:center;justify-content:center;color:#ffd84d;font-size:22px;">🍰</div>'
        )

    thumbnail.short_description = "Imagen"

    def image_preview(self, obj):
        if obj.image_url:
            return format_html(
                '<img src="{}" style="max-width:320px;max-height:220px;border-radius:14px;object-fit:cover;" />',
                obj.image_url,
            )

        return "Sin imagen"

    image_preview.short_description = "Vista previa"

    def stock_status(self, obj):
        if obj.low_stock():
            return format_html(
                '<span style="color:#f87171;font-weight:bold;">Stock bajo</span>'
            )

        return format_html(
            '<span style="color:#4ade80;font-weight:bold;">OK</span>'
        )

    stock_status.short_description = "Estado stock"

    def availability_badge(self, obj):
        if obj.is_available:
            return format_html(
                '<span style="background:#14532d;color:#86efac;padding:4px 10px;border-radius:999px;font-weight:bold;">Activo</span>'
            )

        return format_html(
            '<span style="background:#7f1d1d;color:#fecaca;padding:4px 10px;border-radius:999px;font-weight:bold;">Inactivo</span>'
        )

    availability_badge.short_description = "Disponible"

    @admin.action(description="Marcar productos como disponibles")
    def mark_as_available(self, request, queryset):
        updated = queryset.update(is_available=True)

        self.message_user(
            request,
            f"{updated} productos marcados como disponibles.",
        )

    @admin.action(description="Marcar productos como no disponibles")
    def mark_as_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)

        self.message_user(
            request,
            f"{updated} productos marcados como no disponibles.",
        )