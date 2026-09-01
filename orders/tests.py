from datetime import date, timedelta
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from catalog.models import Product
from core.models import Address
from .models import Order, OrderIssue


class MercaGoFlowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_data", verbosity=0)

    def test_home_only_mercago_has_a_real_link(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, 'href="/mercago/"')
        self.assertContains(response, "Comida")
        self.assertContains(response, "MercaGo")

    def test_catalog_search_and_category_filter(self):
        response = self.client.get(reverse("catalog"), {"q": "tomate"})
        self.assertContains(response, "Tomate perita")
        self.assertNotContains(response, "Banana")
        response = self.client.get(reverse("catalog"), {"category": "frutas"})
        self.assertContains(response, "Banana")
        self.assertNotContains(response, "Tomate perita")

    def test_complete_guest_order_and_issue_response(self):
        product = Product.objects.get(name="Tomate perita")
        self.client.post(reverse("add_to_cart", args=(product.id,)), {"quantity": "34", "next": reverse("catalog")})
        self.client.post(reverse("preferences", args=(product.id,)), {
            "quantity": "34", "freshness": "Maduro", "size": "Mediano",
            "quality": "Mejor calidad", "substitution": "Consultarme",
            "tolerance": "10%", "note": "Firmes y sin golpes",
        })
        response = self.client.post(reverse("checkout"), {
            "guest_name": "Cliente prueba",
            "address": Address.objects.get(label="Casa").id,
            "scheduled_date": (date.today() + timedelta(days=1)).isoformat(),
            "scheduled_window": "10:00 - 12:00",
        })
        order = Order.objects.get()
        self.assertRedirects(response, reverse("order_detail", args=(order.id,)))
        self.assertEqual(order.items.get().preferences["freshness"], "Maduro")
        self.assertEqual(order.service_fee, 15)
        self.assertEqual(order.delivery_fee, 15)
        self.assertEqual(order.estimated_total, 285)
        detail = self.client.get(reverse("order_detail", args=(order.id,)))
        self.assertContains(detail, "Servicio MercaGo")
        self.assertContains(detail, "Envío")
        issue = OrderIssue.objects.create(
            order_item=order.items.get(), type="PRICE_CHANGE",
            message="El precio cambió", proposed_price="9.00",
        )
        order.refresh_from_db()
        self.assertEqual(order.status, "WAITING_CUSTOMER_APPROVAL")
        response = self.client.post(reverse("respond_issue", args=(order.id, issue.id)), {"decision": "accept"})
        self.assertRedirects(response, reverse("order_detail", args=(order.id,)))
        issue.refresh_from_db()
        order.refresh_from_db()
        self.assertEqual(issue.status, "ACCEPTED")
        self.assertEqual(order.status, "SHOPPING")

    def test_rejects_past_delivery_date(self):
        product = Product.objects.first()
        self.client.post(reverse("add_to_cart", args=(product.id,)), {"quantity": "40"})
        response = self.client.post(reverse("checkout"), {
            "guest_name": "Cliente prueba",
            "address": Address.objects.first().id,
            "scheduled_date": (date.today() - timedelta(days=1)).isoformat(),
            "scheduled_window": "10:00 - 12:00",
        })
        self.assertContains(response, "La fecha no puede ser anterior a hoy")
        self.assertFalse(Order.objects.exists())

    def test_minimum_order_is_enforced_server_side(self):
        product = Product.objects.get(name="Tomate perita")
        self.client.post(reverse("add_to_cart", args=(product.id,)), {"quantity": "1"})
        response = self.client.get(reverse("checkout"))
        self.assertRedirects(response, reverse("cart"))
        response = self.client.get(reverse("cart"))
        self.assertContains(response, "Mínimo de compra Bs 250")
        self.assertContains(response, "Faltan Bs 242,50")
        self.assertFalse(Order.objects.exists())

    def test_guest_can_save_and_select_a_delivery_location(self):
        response = self.client.post(reverse("address_create"), {
            "label": "Oficina",
            "address": "Avenida Beni, calle 4, N.º 120",
            "reference": "Puerta azul frente a la farmacia",
            "next": "catalog",
        })
        self.assertRedirects(response, reverse("catalog"))
        address = Address.objects.get(label="Oficina")
        self.assertTrue(address.session_key)
        self.assertEqual(self.client.session["selected_address_id"], address.id)
        catalog = self.client.get(reverse("catalog"))
        self.assertContains(catalog, "Avenida Beni, calle 4, N.º 120")

        other_client = self.client_class()
        other_catalog = other_client.get(reverse("catalog"))
        self.assertNotContains(other_catalog, "Avenida Beni, calle 4, N.º 120")
