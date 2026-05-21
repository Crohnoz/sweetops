from django.contrib import admin
from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = (
        'name',
        'category',
        'sector',
        'price',
        'stock',
        'minimum_stock',
        'is_available',
    )

    search_fields = (
        'name',
        'category',
    )

    list_filter = (
        'category',
        'sector',
        'is_available',
    )