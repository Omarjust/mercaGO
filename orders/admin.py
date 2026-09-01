from django.contrib import admin
from .models import Order, OrderIssue, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "quantity", "estimated_unit_price", "preferences")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "guest_name", "status", "scheduled_date", "service_fee", "delivery_fee", "estimated_total", "final_total")
    list_filter = ("status", "scheduled_date")
    search_fields = ("reference", "guest_name", "address__address")
    inlines = (OrderItemInline,)


@admin.register(OrderIssue)
class OrderIssueAdmin(admin.ModelAdmin):
    list_display = ("order_item", "type", "proposed_price", "status", "created_at")
    list_filter = ("type", "status")
    search_fields = ("order_item__order__reference", "order_item__product__name", "message")
    autocomplete_fields = ()


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("order", "product", "quantity", "status", "estimated_unit_price", "final_unit_price")
    list_filter = ("status",)
