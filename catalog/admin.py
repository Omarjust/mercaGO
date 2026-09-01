from django.contrib import admin
from .models import Category, Market, Product


@admin.register(Market)
class MarketAdmin(admin.ModelAdmin):
    list_display = ("name", "city", "is_available")


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "icon", "order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "unit", "estimated_price", "is_available", "is_fresh")
    list_filter = ("market", "category", "is_available", "is_fresh")
    search_fields = ("name",)
