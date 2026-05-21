from django.urls import path
from .views import sector_view

urlpatterns = [
    path("sector/<str:sector>/", sector_view, name="sector_view"),
]
