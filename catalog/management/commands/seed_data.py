import json
import os
from pathlib import Path

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils.text import slugify

from core.models import Address
from catalog.models import Category, Market, Product


DEFAULT_PRODUCTS_FILE = Path(__file__).resolve().parents[2] / "seed" / "products.json"


class Command(BaseCommand):
    help = "Crea el catálogo, direcciones y usuario administrador de demostración."

    def add_arguments(self, parser):
        parser.add_argument(
            "--products-file",
            type=Path,
            default=DEFAULT_PRODUCTS_FILE,
            help="Archivo JSON con mercado, categorías y productos.",
        )

    def handle(self, *args, **options):
        products_file = options["products_file"]
        try:
            seed = json.loads(products_file.read_text(encoding="utf-8"))
        except FileNotFoundError as exc:
            raise CommandError(f"No existe el archivo seed: {products_file}") from exc
        except json.JSONDecodeError as exc:
            raise CommandError(f"El archivo seed no contiene JSON válido: {exc}") from exc

        market_data = seed.get("market", {})
        if not market_data.get("name"):
            raise CommandError("El seed debe incluir market.name.")

        market, _ = Market.objects.update_or_create(
            name=market_data["name"],
            defaults={
                "city": market_data.get("city", ""),
                "description": market_data.get("description", ""),
                "is_available": market_data.get("is_available", True),
            },
        )
        categories = {}
        for index, category_data in enumerate(seed.get("categories", [])):
            name = category_data.get("name")
            if not name:
                raise CommandError(f"La categoría #{index + 1} no tiene nombre.")
            category, _ = Category.objects.update_or_create(
                slug=category_data.get("slug") or slugify(name),
                defaults={
                    "name": name,
                    "icon": category_data.get("icon", "🧺"),
                    "order": category_data.get("order", index),
                },
            )
            categories[name] = category

        products = seed.get("products", [])
        for index, product_data in enumerate(products):
            name = product_data.get("name")
            category_name = product_data.get("category")
            if not name:
                raise CommandError(f"El producto #{index + 1} no tiene nombre.")
            if category_name not in categories:
                raise CommandError(f"El producto '{name}' usa una categoría inexistente: {category_name}")
            Product.objects.update_or_create(
                market=market,
                name=name,
                defaults={
                    "category": categories[category_name],
                    "unit": product_data.get("unit", "unidad"),
                    "estimated_price": product_data.get("estimated_price", "0.00"),
                    "image": product_data.get("image", "🧺"),
                    "is_available": product_data.get("is_available", True),
                    "is_fresh": product_data.get("is_fresh", True),
                },
            )

        Address.objects.update_or_create(label="Casa", address="Avenida Cruz del Sur, 537", defaults={"reference": "Portón negro, timbre a la derecha"})
        Address.objects.update_or_create(label="Restaurante", address="Equipetrol, calle 8 Oeste", defaults={"reference": "Recepción de proveedores"})

        admin_password = os.getenv("MERCAGO_ADMIN_PASSWORD")
        if admin_password:
            User = get_user_model()
            if not User.objects.filter(username="admin").exists():
                User.objects.create_superuser("admin", "admin@mercago.local", admin_password)
                self.stdout.write(self.style.WARNING("Administrador demo creado desde MERCAGO_ADMIN_PASSWORD."))

        self.stdout.write(self.style.SUCCESS(f"Datos listos: {len(products)} productos, {len(categories)} categorías y 2 direcciones."))
