from collections import defaultdict

from django.core.management.base import BaseCommand

from products.models import Product


def normalize_name(name):
    return (name or "").strip().lower()


def product_score(product):
    score = 0

    if product.olaclick_id:
        score += 100

    if product.image_url:
        score += 50

    if product.is_available:
        score += 20

    if product.description:
        score += 5

    if product.price and product.price > 0:
        score += 3

    return score


class Command(BaseCommand):
    help = "Limpia duplicados conservando productos más completos"

    def handle(self, *args, **options):

        grouped = defaultdict(list)

        for product in Product.objects.all().order_by("id"):

            key = normalize_name(product.name)

            if key:
                grouped[key].append(product)

        removed = 0
        duplicate_groups = 0

        for _, products in grouped.items():

            if len(products) <= 1:
                continue

            duplicate_groups += 1

            sorted_products = sorted(
                products,
                key=product_score,
                reverse=True
            )

            best = sorted_products[0]

            self.stdout.write("")
            self.stdout.write(f"Conservando: {best.name}")
            self.stdout.write(f"ID: {best.id}")
            self.stdout.write(f"OLA: {best.olaclick_id}")
            self.stdout.write(f"IMG: {'SI' if best.image_url else 'NO'}")

            for product in sorted_products[1:]:

                self.stdout.write(
                    f"Eliminado -> "
                    f"{product.name} | "
                    f"ID {product.id} | "
                    f"OLA {product.olaclick_id}"
                )

                product.delete()

                removed += 1

        without_image = Product.objects.filter(
            image_url__isnull=True
        ).count() + Product.objects.filter(
            image_url=""
        ).count()

        self.stdout.write("")
        self.stdout.write("=" * 60)
        self.stdout.write(
            self.style.SUCCESS("LIMPIEZA COMPLETADA")
        )
        self.stdout.write(f"Grupos duplicados: {duplicate_groups}")
        self.stdout.write(f"Productos eliminados: {removed}")
        self.stdout.write(f"Productos sin imagen: {without_image}")