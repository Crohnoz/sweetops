from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST

from orders.models import Order, OrderItem, SectorTicket
from products.models import Product


ACTIVE_STATUSES = ["pending", "in_progress", "ready"]
SECTORS = ["cafeteria", "vitrina", "display"]


def home_view(request):
    counts = {
        sector: SectorTicket.objects.filter(
            sector=sector,
            status__in=ACTIVE_STATUSES
        ).count()
        for sector in SECTORS
    }

    return render(
        request,
        "kitchen/home.html",
        {
            "counts": counts,
        }
    )


def create_order_view(request):
    products = Product.objects.filter(
        is_available=True
    ).order_by("sector", "name")

    if request.method == "POST":
        customer_name = request.POST.get("customer_name", "").strip()
        notes = request.POST.get("notes", "").strip()

        if not customer_name:
            customer_name = "Pedido rápido"

        selected_items = []

        for product in products:
            quantity_raw = request.POST.get(
                f"product_{product.id}",
                "0"
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

        return redirect("/kitchen/")

    return render(
        request,
        "kitchen/create_order.html",
        {
            "products": products,
        },
    )


def sector_view(request, sector):
    tickets = (
        SectorTicket.objects
        .filter(
            sector=sector,
            status__in=ACTIVE_STATUSES
        )
        .select_related("order")
        .prefetch_related(
            "order__items",
            "order__items__product"
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
            status__in=["delivered", "cancelled"]
        )
        .select_related("order")
        .prefetch_related(
            "order__items",
            "order__items__product"
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
        id=ticket_id
    )

    new_status = request.POST.get("status")
    valid_statuses = dict(SectorTicket.STATUS_CHOICES)

    if new_status in valid_statuses:
        ticket.status = new_status
        ticket.save(update_fields=["status"])

        order = ticket.order

        all_tickets_delivered = not order.sector_tickets.exclude(
            status__in=["delivered", "cancelled"]
        ).exists()

        if all_tickets_delivered:
            order.status = "completed"
            order.save(update_fields=["status"])

    return redirect(
        f"/kitchen/sector/{ticket.sector}/"
    )