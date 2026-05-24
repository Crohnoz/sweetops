from django.core.management.base import BaseCommand

from products.models import Product


class Command(BaseCommand):
    help = "Reporta productos sin imagen"

    def handle(self, *args, **options):
        products = Product.objects.filter(
            image_url__isnull=True
        ) | Product.objects.filter(
            image_url=""
        )

        products = products.order_by("category", "name")

        self.stdout.write("")
        self.stdout.write("PRODUCTOS SIN IMAGEN")
        self.stdout.write("-" * 60)

        for product in products:
            self.stdout.write(
                f"{product.name} | {product.category} | {product.sector} | ${product.price} | ola_id={product.olaclick_id or 'SIN_ID'}"
            )

        self.stdout.write("-" * 60)
        self.stdout.write(f"Total sin imagen: {products.count()}")