from django.shortcuts import render
from orders.models import SectorTicket


def sector_view(request, sector):
    tickets = SectorTicket.objects.filter(
        sector=sector
    ).order_by("-created_at")

    return render(
        request,
        "kitchen/sector.html",
        {
            "sector": sector,
            "tickets": tickets,
        }
    )

# Create your views here.
