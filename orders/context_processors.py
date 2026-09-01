from decimal import Decimal
from django.db.models import Q
from core.models import Address
from .cart import DELIVERY_FEE, MINIMUM_ORDER_TOTAL, SERVICE_FEE, cart_entries


def cart_summary(request):
    session_key = request.session.session_key or ""
    address_filter = Q(session_key="") | Q(session_key=session_key)
    if request.user.is_authenticated:
        address_filter |= Q(user=request.user)
    selected_id = request.session.get("selected_address_id")
    addresses = Address.objects.filter(address_filter)
    current_address = addresses.filter(id=selected_id).first() or addresses.first()
    try:
        entries, total = cart_entries(request)
        return {
            "cart_count": len(entries),
            "cart_estimated_total": total,
            "minimum_order_total": MINIMUM_ORDER_TOTAL,
            "minimum_remaining": max(Decimal("0"), MINIMUM_ORDER_TOTAL - total),
            "minimum_reached": total >= MINIMUM_ORDER_TOTAL,
            "service_fee": SERVICE_FEE,
            "delivery_fee": DELIVERY_FEE,
            "cart_grand_total": total + SERVICE_FEE + DELIVERY_FEE,
            "current_address": current_address,
        }
    except Exception:
        return {
            "cart_count": 0, "cart_estimated_total": 0,
            "minimum_order_total": MINIMUM_ORDER_TOTAL,
            "minimum_remaining": MINIMUM_ORDER_TOTAL,
            "minimum_reached": False,
            "service_fee": SERVICE_FEE,
            "delivery_fee": DELIVERY_FEE,
            "cart_grand_total": SERVICE_FEE + DELIVERY_FEE,
            "current_address": current_address,
        }
