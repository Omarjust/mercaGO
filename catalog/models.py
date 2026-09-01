from django.db import models


class Market(models.Model):
    name = models.CharField(max_length=120)
    city = models.CharField(max_length=120)
    description = models.CharField(max_length=240, blank=True)
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=80, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField(max_length=10, default="🧺")
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("order", "name")
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.name


class Product(models.Model):
    UNIT_CHOICES = [
        ("kg", "kg"), ("unidad", "unidad"), ("docena", "docena"),
        ("paquete", "paquete"), ("bolsa", "bolsa"),
    ]
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=140)
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES)
    estimated_price = models.DecimalField(max_digits=8, decimal_places=2)
    image = models.CharField(max_length=20, default="🧺", help_text="Emoji o referencia visual")
    is_available = models.BooleanField(default=True)
    is_fresh = models.BooleanField(default=True)

    class Meta:
        ordering = ("category__order", "name")

    def __str__(self):
        return self.name
