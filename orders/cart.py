from decimal import Decimal
from catalog.models import Product

CART_KEY = "mercago_cart"
MINIMUM_ORDER_TOTAL = Decimal("250.00")
SERVICE_FEE = Decimal("15.00")
DELIVERY_FEE = Decimal("15.00")


def get_cart(request):
    return request.session.get(CART_KEY, {})


def save_cart(request, cart):
    request.session[CART_KEY] = cart
    request.session.modified = True


def cart_entries(request):
    cart = get_cart(request)
    products = Product.objects.filter(id__in=cart.keys()).select_related("category")
    entries, total = [], Decimal("0")
    for product in products:
        data = cart.get(str(product.id), {})
        quantity = Decimal(str(data.get("quantity", 1)))
        line_total = product.estimated_price * quantity
        total += line_total
        entries.append({"product": product, "quantity": quantity, "line_total": line_total, "preferences": data.get("preferences", {})})
    return entries, total
