import uuid
from django.conf import settings
from django.db import models
from core.models import Address
from catalog.models import Product


class Order(models.Model):
    STATUS_CHOICES = [
        ("CONFIRMED", "Pedido confirmado"),
        ("BUYER_ASSIGNED", "Comprador asignado"),
        ("SHOPPING", "Comprando en el mercado"),
        ("WAITING_CUSTOMER_APPROVAL", "Esperando tu aprobación"),
        ("SHOPPING_COMPLETED", "Compra terminada"),
        ("AT_BUFFER", "Verificando productos"),
        ("READY_FOR_DELIVERY", "Listo para entrega"),
        ("OUT_FOR_DELIVERY", "En camino"),
        ("DELIVERED", "Entregado"),
        ("CANCELLED", "Cancelado"),
    ]
    WINDOW_CHOICES = [
        ("08:00 - 10:00", "08:00 - 10:00"),
        ("10:00 - 12:00", "10:00 - 12:00"),
        ("14:00 - 16:00", "14:00 - 16:00"),
        ("16:00 - 18:00", "16:00 - 18:00"),
    ]
    reference = models.CharField(max_length=12, unique=True, editable=False)
    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    guest_name = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=40, choices=STATUS_CHOICES, default="CONFIRMED")
    address = models.ForeignKey(Address, on_delete=models.PROTECT)
    scheduled_date = models.DateField()
    scheduled_window = models.CharField(max_length=30, choices=WINDOW_CHOICES)
    estimated_total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    service_fee = models.DecimalField(max_digits=8, decimal_places=2, default=15)
    delivery_fee = models.DecimalField(max_digits=8, decimal_places=2, default=15)
    final_total = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = f"MG-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.reference} · {self.get_status_display()}"

    @property
    def display_total(self):
        return self.final_total if self.final_total is not None else self.estimated_total

    @property
    def products_subtotal(self):
        return sum((item.estimated_line_total for item in self.items.all()), 0)


class OrderItem(models.Model):
    ITEM_STATUS = [
        ("PENDING", "Pendiente"), ("FOUND", "Encontrado"),
        ("SUBSTITUTED", "Sustituido"), ("NOT_PURCHASED", "No comprado"),
    ]
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=7, decimal_places=2)
    estimated_unit_price = models.DecimalField(max_digits=8, decimal_places=2)
    final_unit_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    preferences = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=24, choices=ITEM_STATUS, default="PENDING")

    @property
    def estimated_line_total(self):
        return self.quantity * self.estimated_unit_price

    def __str__(self):
        return f"{self.product} × {self.quantity}"


class OrderIssue(models.Model):
    TYPE_CHOICES = [
        ("PRICE_CHANGE", "Cambio de precio"),
        ("OUT_OF_STOCK", "Producto agotado"),
        ("SUBSTITUTION", "Sustitución"),
    ]
    STATUS_CHOICES = [("PENDING", "Pendiente"), ("ACCEPTED", "Aceptada"), ("REJECTED", "Rechazada")]
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name="issues")
    type = models.CharField(max_length=24, choices=TYPE_CHOICES)
    message = models.TextField()
    proposed_product_name = models.CharField(max_length=140, blank=True)
    proposed_price = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-created_at",)
        verbose_name = "Incidencia"
        verbose_name_plural = "Incidencias"

    def __str__(self):
        return f"{self.get_type_display()} · {self.order_item.product}"

    def save(self, *args, **kwargs):
        creating_pending = self._state.adding and self.status == "PENDING"
        super().save(*args, **kwargs)
        if creating_pending:
            order = self.order_item.order
            if order.status not in ("DELIVERED", "CANCELLED"):
                order.status = "WAITING_CUSTOMER_APPROVAL"
                order.save(update_fields=("status",))
