from django.db import models
from django.utils import timezone

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
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(blank=True, null=True)

    def calculate_total(self):
        self.total = sum(item.subtotal for item in self.items.all())
        self.save(update_fields=["total", "updated_at"])
        return self.total

    def generate_sector_tickets(self):
        sectors = (
            self.items
            .exclude(sector_snapshot="")
            .values_list("sector_snapshot", flat=True)
            .distinct()
        )

        for sector in sectors:
            SectorTicket.objects.get_or_create(
                order=self,
                sector=sector,
            )

    def refresh_status_from_tickets(self):
        tickets = self.sector_tickets.all()

        if not tickets.exists():
            return

        now = timezone.now()

        if tickets.filter(status="cancelled").count() == tickets.count():
            self.status = "cancelled"

            if not self.completed_at:
                self.completed_at = now

        elif not tickets.exclude(status__in=["delivered", "cancelled"]).exists():
            self.status = "completed"

            if not self.completed_at:
                self.completed_at = now

        elif tickets.filter(status__in=["in_progress", "ready"]).exists():
            self.status = "in_progress"
            self.completed_at = None

        else:
            self.status = "pending"
            self.completed_at = None

        self.save(update_fields=["status", "completed_at", "updated_at"])

    @property
    def display_name(self):
        return self.customer_name or f"Pedido #{self.id}"

    @property
    def item_count(self):
        return self.items.count()

    @property
    def total_units(self):
        return sum(item.quantity for item in self.items.all())

    @property
    def duration_minutes(self):
        if not self.completed_at:
            return None

        delta = self.completed_at - self.created_at

        return round(delta.total_seconds() / 60, 1)

    def __str__(self):
        return f"{self.display_name} - ${self.total}"


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

    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.unit_price:
            self.unit_price = self.product.price

        if not self.sector_snapshot:
            self.sector_snapshot = self.product.sector

        self.subtotal = self.quantity * self.unit_price

        super().save(*args, **kwargs)

        self.order.calculate_total()
        self.order.generate_sector_tickets()

    def delete(self, *args, **kwargs):
        order = self.order

        super().delete(*args, **kwargs)

        order.calculate_total()
        order.generate_sector_tickets()

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
    updated_at = models.DateTimeField(auto_now=True)
    ready_at = models.DateTimeField(blank=True, null=True)
    delivered_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        unique_together = ("order", "sector")
        ordering = ["created_at"]

    def save(self, *args, **kwargs):
        now = timezone.now()

        if self.status == "ready" and not self.ready_at:
            self.ready_at = now

        if self.status == "delivered" and not self.delivered_at:
            self.delivered_at = now

        super().save(*args, **kwargs)

        self.order.refresh_status_from_tickets()

    @property
    def preparation_minutes(self):
        if not self.ready_at:
            return None

        delta = self.ready_at - self.created_at

        return round(delta.total_seconds() / 60, 1)

    @property
    def delivery_minutes(self):
        if not self.delivered_at:
            return None

        delta = self.delivered_at - self.created_at

        return round(delta.total_seconds() / 60, 1)

    def __str__(self):
        return f"Comanda {self.sector} - Pedido #{self.order.id}"