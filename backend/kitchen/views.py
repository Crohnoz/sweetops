from django.db.models import Count, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from orders.models import Order, OrderItem, SectorTicket
from products.models import Product


ACTIVE_STATUSES = ["pending", "in_progress", "ready"]
FINISHED_STATUSES = ["delivered", "cancelled"]

SECTORS = ["cafeteria", "display"]

CATEGORY_ORDER = [
    "coffee",
    "waffle",
    "cupcake",
    "cake",
    "dessert",
    "icecream",
    "frappe",
    "drink",
    "promo",
    "other",
]


def home_view(request):
    today = timezone.localdate()

    counts = {
        sector: SectorTicket.objects.filter(
            sector=sector,
            status__in=ACTIVE_STATUSES,
        ).count()
        for sector in SECTORS
    }

    active_orders = Order.objects.filter(
        status__in=["pending", "in_progress"],
    ).count()

    completed_today = Order.objects.filter(
        status="completed",
        completed_at__date=today,
    )

    sales_today = completed_today.aggregate(
        total=Sum("total")
    )["total"] or 0

    completed_orders_today = completed_today.count()

    average_ticket = (
        sales_today / completed_orders_today
        if completed_orders_today > 0
        else 0
    )

    pending_tickets = SectorTicket.objects.filter(
        status="pending",
    ).count()

    ready_tickets = SectorTicket.objects.filter(
        status="ready",
    ).count()

    return render(
        request,
        "kitchen/home.html",
        {
            "counts": counts,
            "active_orders": active_orders,
            "sales_today": sales_today,
            "completed_orders_today": completed_orders_today,
            "average_ticket": average_ticket,
            "pending_tickets": pending_tickets,
            "ready_tickets": ready_tickets,
        },
    )


def create_order_view(request):
    products = (
        Product.objects
        .filter(is_available=True)
        .order_by("category", "name")
    )

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        notes = request.POST.get("notes", "").strip()

        if not customer_name:
            customer_name = "Pedido rápido"

        selected_items = []

        for product in products:
            quantity_raw = request.POST.get(
                f"product_{product.id}",
                "0",
            )

            try:
                quantity = int(quantity_raw)
            except ValueError:
                quantity = 0

            if quantity > 0:
                selected_items.append(
                    {
                        "product": product,
                        "quantity": quantity,
                    }
                )

        if not selected_items:
            return redirect("/kitchen/create-order/")

        order = Order.objects.create(
            customer_name=customer_name,
            notes=notes,
            status="pending",
        )

        for item in selected_items:
            product = item["product"]
            quantity = item["quantity"]

            OrderItem.objects.create(
                order=order,
                product=product,
                quantity=quantity,
                unit_price=product.price,
                sector_snapshot=product.sector,
            )

        order.calculate_total()
        order.generate_sector_tickets()
        order.refresh_status_from_tickets()

        return redirect("/kitchen/")

    return render(
        request,
        "kitchen/create_order.html",
        {
            "products": products,
            "category_order": CATEGORY_ORDER,
        },
    )


def sector_view(request, sector):
    tickets = (
        SectorTicket.objects
        .filter(
            sector=sector,
            status__in=ACTIVE_STATUSES,
        )
        .select_related("order")
        .prefetch_related(
            "order__items",
            "order__items__product",
        )
        .order_by("created_at")
    )

    return render(
        request,
        "kitchen/sector.html",
        {
            "sector": sector,
            "tickets": tickets,
        },
    )


def sector_history_view(request, sector):
    tickets = (
        SectorTicket.objects
        .filter(
            sector=sector,
            status__in=FINISHED_STATUSES,
        )
        .select_related("order")
        .prefetch_related(
            "order__items",
            "order__items__product",
        )
        .order_by("-created_at")[:50]
    )

    return render(
        request,
        "kitchen/history.html",
        {
            "sector": sector,
            "tickets": tickets,
        },
    )


@require_POST
def update_ticket_status(request, ticket_id):
    ticket = get_object_or_404(
        SectorTicket,
        id=ticket_id,
    )

    new_status = request.POST.get("status")
    valid_statuses = dict(SectorTicket.STATUS_CHOICES)

    if new_status in valid_statuses:
        ticket.status = new_status
        ticket.save(update_fields=["status", "updated_at", "ready_at", "delivered_at"])

    return redirect(
        f"/kitchen/sector/{ticket.sector}/"
    )