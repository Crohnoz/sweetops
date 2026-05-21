import json
from pathlib import Path

from django.core.management.base import BaseCommand

from products.models import Product


def detect_sector(category_name, product_name):
    text = f"{category_name} {product_name}".lower()

    if any(word in text for word in ["café", "latte", "capuchino", "mocaccino", "espresso", "té", "milkshake", "frappe", "jugo", "limonada", "bebida", "agua", "redbull"]):
        return "cafeteria"

    if any(word in text for word in ["sandwich", "sándwich", "vitrina", "cupcake", "torta", "pie", "cheesecake", "kuchen", "alfajor", "waffle", "helado", "dulce"]):
        return "display"

    return "kitchen"


def detect_category(category_name, product_name):
    text = f"{category_name} {product_name}".lower()

    if "cupcake" in text:
        return "cupcake"
    if any(word in text for word in ["café", "latte", "capuchino", "mocaccino", "espresso", "té"]):
        return "coffee"
    if any(word in text for word in ["jugo", "limonada", "bebida", "agua", "redbull", "milkshake", "frappe"]):
        return "drink"
    if any(word in text for word in ["torta", "pie", "cheesecake", "kuchen", "alfajor", "dulce", "cake pop", "cuchufli"]):
        return "dessert"

    return "other"


class Command(BaseCommand):
    help = "Importa productos desde olaclick_products.json"

    def handle(self, *args, **options):
        file_path = Path("olaclick_products.json")

        if not file_path.exists():
            self.stderr.write("No existe olaclick_products.json en la carpeta backend.")
            return

        with file_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        categories = payload.get("data", [])

        created = 0
        updated = 0
        skipped = 0

        for category in categories:
            category_name = category.get("name", "Sin categoría")
            products = category.get("products", [])

            for item in products:
                name = item.get("name")

                if not name:
                    skipped += 1
                    continue

                variants = item.get("product_variants", [])
                first_variant = variants[0] if variants else {}

                price = first_variant.get("price") or 0
                stock = first_variant.get("stock") or 0
                minimum_stock = first_variant.get("stock_threshold") or 5

                product_category = detect_category(category_name, name)
                sector = detect_sector(category_name, name)

                product, was_created = Product.objects.update_or_create(
                    name=name,
                    defaults={
                        "category": product_category,
                        "description": item.get("description") or "",
                        "price": price,
                        "sector": sector,
                        "stock": stock,
                        "minimum_stock": minimum_stock,
                        "is_available": item.get("visible", True),
                    },
                )

                if was_created:
                    created += 1
                else:
                    updated += 1

        self.stdout.write(self.style.SUCCESS("Importación completada"))
        self.stdout.write(f"Creados: {created}")
        self.stdout.write(f"Actualizados: {updated}")
        self.stdout.write(f"Omitidos: {skipped}")
