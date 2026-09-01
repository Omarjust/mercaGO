from decimal import Decimal
from django.db import migrations


def include_fees_in_existing_totals(apps, schema_editor):
    Order = apps.get_model("orders", "Order")
    OrderItem = apps.get_model("orders", "OrderItem")
    for order in Order.objects.all():
        products_total = sum(
            (item.quantity * item.estimated_unit_price for item in OrderItem.objects.filter(order_id=order.id)),
            Decimal("0"),
        )
        order.estimated_total = products_total + order.service_fee + order.delivery_fee
        order.save(update_fields=("estimated_total",))


class Migration(migrations.Migration):
    dependencies = [("orders", "0002_order_delivery_fee_order_service_fee")]
    operations = [migrations.RunPython(include_fees_in_existing_totals, migrations.RunPython.noop)]
