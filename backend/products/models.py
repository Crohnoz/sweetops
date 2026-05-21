from django.db import models


class Product(models.Model):

    SECTOR_CHOICES = [
        ('kitchen', 'Cocina'),
        ('cafeteria', 'Cafetería'),
        ('display', 'Vitrina'),
    ]

    CATEGORY_CHOICES = [
        ('cake', 'Tortas'),
        ('cupcake', 'Cupcakes'),
        ('coffee', 'Cafetería'),
        ('dessert', 'Postres'),
        ('drink', 'Bebidas'),
        ('other', 'Otros'),
    ]

    name = models.CharField(max_length=255)

    category = models.CharField(
        max_length=50,
        choices=CATEGORY_CHOICES
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    sector = models.CharField(
        max_length=20,
        choices=SECTOR_CHOICES
    )

    stock = models.IntegerField(default=0)

    minimum_stock = models.IntegerField(default=5)

    is_available = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def low_stock(self):
        return self.stock <= self.minimum_stock

    def __str__(self):
        return self.name