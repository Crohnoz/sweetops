from django.db import models
from products.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("in_progress", "En preparación"),
        ("completed", "Completado"),
        ("cancelled", "Cancelado"),
    ]

    customer_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def calculate_total(self):
        self.total = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=["total"])
        return self.total

    def generate_sector_tickets(self):
        sectors = self.items.values_list("sector_snapshot", flat=True).distinct()

        for sector in sectors:
            if sector:
                SectorTicket.objects.get_or_create(
                    order=self,
                    sector=sector,
                )

    def __str__(self):
        return f"Pedido #{self.id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)

    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True,
    )

    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    sector_snapshot = models.CharField(
        max_length=20,
        blank=True,
    )

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price

        if not self.sector_snapshot:
            self.sector_snapshot = self.product.sector

        self.subtotal = self.quantity * self.unit_price

        super().save(*args, **kwargs)

        self.order.calculate_total()
        self.order.generate_sector_tickets()

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"


class SectorTicket(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pendiente"),
        ("in_progress", "En preparación"),
        ("ready", "Listo"),
        ("delivered", "Entregado"),
        ("cancelled", "Cancelado"),
    ]

    order = models.ForeignKey(
        Order,
        related_name="sector_tickets",
        on_delete=models.CASCADE,
    )

    sector = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    printed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Comanda {self.sector} - Pedido #{self.order.id}"