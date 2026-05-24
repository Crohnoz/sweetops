from django.urls import path

from .views import (
    home_view,
    create_order_view,
    sector_view,
    sector_history_view,
    update_ticket_status,
)


urlpatterns = [
    path("", home_view, name="kitchen_home"),
    path("create-order/", create_order_view, name="create_order"),
    path("sector/<str:sector>/", sector_view, name="sector_view"),
    path("sector/<str:sector>/history/", sector_history_view, name="sector_history"),
    path("ticket/<int:ticket_id>/status/", update_ticket_status, name="update_ticket_status"),
]