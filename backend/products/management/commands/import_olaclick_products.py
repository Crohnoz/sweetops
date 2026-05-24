import json
import re

from pathlib import Path

from django.core.management.base import BaseCommand
from django.db.models import Count

from products.models import Product


FAVORITE_WORDS = [
    "americano",
    "latte",
    "capuchino",
    "cappuccino",
    "espresso",
    "waffle",
    "frappe",
    "frappé",
    "cupcake",
    "sandwich",
    "sándwich",
]


def product_has_field(field_name):
    return any(
        field.name == field_name
        for field in Product._meta.fields
    )


def clean_name(name):
    if not name:
        return ""

    name = name.strip()
    name = re.sub(r"\s+", " ", name)

    return name


def detect_sector(category_name, product_name):
    text = f"{category_name} {product_name}".lower()

    cafeteria_words = [
        "café",
        "cafe",
        "latte",
        "capuchino",
        "cappuccino",
        "mocaccino",
        "espresso",
        "té",
        "te",
        "milkshake",
        "frappe",
        "frappé",
        "jugo",
        "limonada",
        "bebida",
        "agua",
        "redbull",
    ]

    display_words = [
        "sandwich",
        "sándwich",
        "cupcake",
        "torta",
        "pie",
        "cheesecake",
        "kuchen",
        "alfajor",
        "waffle",
        "helado",
        "brownie",
        "postre",
        "cake pop",
        "cuchufli",
        "promo",
        "promoción",
        "promocion",
    ]

    if any(word in text for word in cafeteria_words):
        return "cafeteria"

    if any(word in text for word in display_words):
        return "display"

    return "display"


def detect_category(category_name, product_name):
    text = f"{category_name} {product_name}".lower()

    mapping = {
        "waffle": "waffle",
        "cupcake": "cupcake",
        "frappe": "frappe",
        "frappé": "frappe",
        "milkshake": "frappe",
        "helado": "icecream",
        "ice cream": "icecream",
        "torta": "cake",
        "cake": "cake",
        "promo": "promo",
        "promoción": "promo",
        "promocion": "promo",
    }

    for key, value in mapping.items():
        if key in text:
            return value

    coffee_words = [
        "café",
        "cafe",
        "latte",
        "capuchino",
        "cappuccino",
        "mocaccino",
        "espresso",
        "té",
        "te",
    ]

    if any(word in text for word in coffee_words):
        return "coffee"

    drink_words = [
        "jugo",
        "limonada",
        "bebida",
        "agua",
        "redbull",
    ]

    if any(word in text for word in drink_words):
        return "drink"

    dessert_words = [
        "pie",
        "cheesecake",
        "kuchen",
        "alfajor",
        "brownie",
        "postre",
        "cake pop",
        "cuchufli",
    ]

    if any(word in text for word in dessert_words):
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


def is_favorite(name):
    text = name.lower()

    return any(
        word in text
        for word in FAVORITE_WORDS
    )


def get_product_score(product):
    score = 0

    if product.image_url:
        score += 100

    if product.olaclick_id:
        score += 80

    if product.is_available:
        score += 40

    if product.price and product.price > 0:
        score += 20

    if product.description:
        score += 10

    return score


class Command(BaseCommand):
    help = "Importa productos OlaClick de forma inteligente y evita duplicados"

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
        has_is_favorite = product_has_field("is_favorite")

        with file_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)

        categories = payload.get("data", [])

        created = 0
        updated = 0
        skipped = 0
        disabled_duplicates = 0
        deleted_duplicates = 0

        imported_names = set()

        for category in categories:
            category_name = category.get("name", "Sin categoría")
            products = category.get("products", [])

            for item in products:
                name = clean_name(item.get("name"))
                olaclick_id = item.get("id")

                if not name:
                    skipped += 1
                    continue

                normalized_name = name.lower()

                if normalized_name in imported_names:
                    skipped += 1
                    continue

                imported_names.add(normalized_name)

                variants = item.get("product_variants", [])
                first_variant = variants[0] if variants else {}

                price = first_variant.get("price") or 0

                if price <= 0:
                    skipped += 1
                    continue

                stock = first_variant.get("stock") or 0
                minimum_stock = first_variant.get("stock_threshold") or 5
                image_url = get_image_url(item)

                defaults = {
                    "category": detect_category(category_name, name),
                    "description": item.get("description") or "",
                    "price": price,
                    "sector": detect_sector(category_name, name),
                    "stock": stock,
                    "minimum_stock": minimum_stock,
                    "is_available": item.get("visible", True),
                }

                if has_image_url:
                    defaults["image_url"] = image_url

                if has_is_favorite:
                    defaults["is_favorite"] = is_favorite(name)

                existing = None

                if has_olaclick_id and olaclick_id:
                    existing = Product.objects.filter(
                        olaclick_id=olaclick_id
                    ).first()

                if not existing:
                    existing = Product.objects.filter(
                        name__iexact=name
                    ).first()

                if existing:
                    for key, value in defaults.items():
                        if key == "image_url" and existing.image_url and not value:
                            continue

                        setattr(existing, key, value)

                    existing.name = name

                    if has_olaclick_id:
                        existing.olaclick_id = olaclick_id

                    existing.save()

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

        duplicates = (
            Product.objects
            .values("name")
            .annotate(total=Count("id"))
            .filter(total__gt=1)
        )

        for duplicate in duplicates:
            duplicated_products = list(
                Product.objects.filter(
                    name=duplicate["name"]
                )
            )

            if len(duplicated_products) <= 1:
                continue

            keep = sorted(
                duplicated_products,
                key=get_product_score,
                reverse=True,
            )[0]

            for product in duplicated_products:
                if product.id == keep.id:
                    continue

                if product.orderitem_set.exists():
                    product.is_available = False
                    product.save(update_fields=["is_available"])
                    disabled_duplicates += 1
                else:
                    product.delete()
                    deleted_duplicates += 1

        self.stdout.write(
            self.style.SUCCESS("Importación completada")
        )

        self.stdout.write(f"Creados: {created}")
        self.stdout.write(f"Actualizados: {updated}")
        self.stdout.write(f"Omitidos: {skipped}")
        self.stdout.write(f"Duplicados desactivados por tener pedidos: {disabled_duplicates}")
        self.stdout.write(f"Duplicados eliminados: {deleted_duplicates}")