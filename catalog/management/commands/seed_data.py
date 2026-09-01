import os
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from core.models import Address
from catalog.models import Category, Market, Product


class Command(BaseCommand):
    help = "Crea el catálogo, direcciones y usuario administrador de demostración."

    def handle(self, *args, **options):
        market, _ = Market.objects.update_or_create(
            name="Mercado Abasto",
            defaults={"city": "Santa Cruz de la Sierra", "description": "Productos frescos elegidos por expertos", "is_available": True},
        )
        category_data = [
            ("Frutas", "🍊"), ("Verduras", "🥕"), ("Carnes", "🥩"),
            ("Pollo", "🍗"), ("Abarrotes", "🛒"), ("Lácteos", "🥛"), ("Otros", "🧺"),
        ]
        categories = {}
        for order, (name, icon) in enumerate(category_data):
            category, _ = Category.objects.update_or_create(slug=slugify(name), defaults={"name": name, "icon": icon, "order": order})
            categories[name] = category

        products = [
            ("Tomate perita", "Verduras", "kg", "7.50", "🍅", True),
            ("Papa holandesa", "Verduras", "kg", "7.00", "🥔", True),
            ("Cebolla morada", "Verduras", "kg", "8.50", "🧅", True),
            ("Zanahoria", "Verduras", "kg", "6.50", "🥕", True),
            ("Lechuga romana", "Verduras", "unidad", "6.00", "🥬", True),
            ("Banana", "Frutas", "kg", "8.00", "🍌", True),
            ("Manzana roja", "Frutas", "kg", "17.00", "🍎", True),
            ("Naranja", "Frutas", "kg", "9.00", "🍊", True),
            ("Limón", "Frutas", "kg", "12.00", "🍋", True),
            ("Pollo entero", "Pollo", "kg", "23.00", "🍗", True),
            ("Pechuga de pollo", "Pollo", "kg", "35.00", "🥩", True),
            ("Carne molida especial", "Carnes", "kg", "49.00", "🥩", True),
            ("Arroz grano largo", "Abarrotes", "bolsa", "12.50", "🍚", False),
            ("Azúcar blanca", "Abarrotes", "bolsa", "8.00", "🧂", False),
            ("Aceite vegetal", "Abarrotes", "unidad", "15.50", "🫗", False),
            ("Harina", "Abarrotes", "paquete", "9.00", "🌾", False),
            ("Leche entera", "Lácteos", "unidad", "8.50", "🥛", False),
            ("Queso criollo", "Lácteos", "kg", "42.00", "🧀", True),
            ("Huevos de granja", "Otros", "docena", "17.00", "🥚", True),
        ]
        for name, category, unit, price, image, is_fresh in products:
            Product.objects.update_or_create(
                market=market, name=name,
                defaults={"category": categories[category], "unit": unit, "estimated_price": price, "image": image, "is_available": True, "is_fresh": is_fresh},
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
