import json
from pathlib import Path

from django.core.management.base import BaseCommand

from products.models import Product


def product_has_field(field_name):
    return any(field.name == field_name for field in Product._meta.fields)


def detect_sector(category_name, product_name):
    text = f"{category_name} {product_name}".lower()

    cafeteria_words = [
        "café", "cafe", "latte", "capuchino", "cappuccino",
        "mocaccino", "espresso", "té", "te", "milkshake",
        "frappe", "frappé", "jugo", "limonada", "bebida",
        "agua", "redbull"
    ]

    display_words = [
        "sandwich", "sándwich", "vitrina", "cupcake", "torta",
        "pie", "cheesecake", "kuchen", "alfajor", "waffle",
        "helado", "dulce", "brownie", "postre", "cake pop",
        "cuchufli", "promo", "promoción", "promocion"
    ]

    if any(word in text for word in cafeteria_words):
        return "cafeteria"

    if any(word in text for word in display_words):
        return "display"

    return "display"


def detect_category(category_name, product_name):
    text = f"{category_name} {product_name}".lower()

    if "waffle" in text:
        return "waffle"

    if "cupcake" in text:
        return "cupcake"

    if any(word in text for word in [
        "café", "cafe", "latte", "capuchino", "cappuccino",
        "mocaccino", "espresso", "té", "te"
    ]):
        return "coffee"

    if any(word in text for word in ["frappe", "frappé", "milkshake"]):
        return "frappe"

    if any(word in text for word in ["helado", "ice cream"]):
        return "icecream"

    if any(word in text for word in ["torta", "cake"]):
        return "cake"

    if any(word in text for word in ["promo", "promoción", "promocion"]):
        return "promo"

    if any(word in text for word in ["jugo", "limonada", "bebida", "agua", "redbull"]):
        return "drink"

    if any(word in text for word in [
        "pie", "cheesecake", "kuchen", "alfajor", "dulce",
        "brownie", "postre", "cake pop", "cuchufli"
    ]):
        return "dessert"

    return "other"


def get_image_url(item):
    images = item.get("images", [])

    if not images:
        return None

    first_image = images[0]

    return (
        first_image.get("image_url")
        or first_image.get("url")
        or None
    )


def find_existing_product(name, olaclick_id, has_olaclick_id):
    if has_olaclick_id and olaclick_id:
        product = Product.objects.filter(
            olaclick_id=olaclick_id
        ).first()

        if product:
            return product

    return Product.objects.filter(
        name__iexact=name
    ).first()


class Command(BaseCommand):
    help = "Importa productos desde olaclick_products.json evitando duplicados"

    def handle(self, *args, **options):
        file_path = Path("olaclick_products.json")

        if not file_path.exists():
            self.stderr.write(
                self.style.ERROR(
                    "No existe olaclick_products.json en la carpeta backend."
                )
            )
            return

        has_image_url = product_has_field("image_url")
        has_olaclick_id = product_has_field("olaclick_id")

        with file_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        categories = payload.get("data", [])

        created = 0
        updated = 0
        skipped = 0
        without_image = 0

        for category in categories:
            category_name = category.get("name", "Sin categoría")
            products = category.get("products", [])

            for item in products:
                name = (item.get("name") or "").strip()
                olaclick_id = item.get("id")

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
                image_url = get_image_url(item)

                if not image_url:
                    without_image += 1

                defaults = {
                    "category": product_category,
                    "description": item.get("description") or "",
                    "price": price,
                    "sector": sector,
                    "stock": stock,
                    "minimum_stock": minimum_stock,
                    "is_available": item.get("visible", True),
                }

                if has_image_url:
                    defaults["image_url"] = image_url

                existing_product = find_existing_product(
                    name=name,
                    olaclick_id=olaclick_id,
                    has_olaclick_id=has_olaclick_id,
                )

                if existing_product:
                    for key, value in defaults.items():
                        setattr(existing_product, key, value)

                    existing_product.name = name

                    if has_olaclick_id:
                        existing_product.olaclick_id = olaclick_id

                    existing_product.save()

                    updated += 1

                else:
                    create_data = {
                        "name": name,
                        **defaults,
                    }

                    if has_olaclick_id:
                        create_data["olaclick_id"] = olaclick_id

                    Product.objects.create(**create_data)

                    created += 1

        self.stdout.write(self.style.SUCCESS("Importación completada"))
        self.stdout.write(f"Creados: {created}")
        self.stdout.write(f"Actualizados: {updated}")
        self.stdout.write(f"Omitidos: {skipped}")
        self.stdout.write(f"Sin imagen desde OlaClick: {without_image}")

        if not has_image_url:
            self.stdout.write(
                self.style.WARNING(
                    "Aviso: Product aún no tiene campo image_url. Se importó sin imágenes."
                )
            )

        if not has_olaclick_id:
            self.stdout.write(
                self.style.WARNING(
                    "Aviso: Product aún no tiene campo olaclick_id. Se usó name como identificador."
                )
            )