from django.db import models
from products.models import Product


class Order(models.Model):

    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Efectivo'),
        ('card', 'Tarjeta'),
        ('transfer', 'Transferencia'),
        ('other', 'Otro'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('in_progress', 'En preparación'),
        ('completed', 'Completado'),
        ('cancelled', 'Cancelado'),
    ]

    customer_name = models.CharField(max_length=255, blank=True, null=True)

    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='cash'
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def calculate_total(self):
        total = sum(item.subtotal for item in self.items.all())
        self.total = total
        self.save()
        return total

    def __str__(self):
        return f"Pedido #{self.id} - {self.customer_name or 'Cliente sin nombre'}"


class OrderItem(models.Model):

    order = models.ForeignKey(
        Order,
        related_name='items',
        on_delete=models.CASCADE
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT
    )

    quantity = models.PositiveIntegerField(default=1)

    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price

        self.subtotal = self.quantity * self.unit_price

        super().save(*args, **kwargs)

        self.order.calculate_total()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"