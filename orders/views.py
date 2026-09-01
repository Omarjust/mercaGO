from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.db import transaction
from django.http import HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST
from catalog.models import Product
from .cart import DELIVERY_FEE, MINIMUM_ORDER_TOTAL, SERVICE_FEE, cart_entries, get_cart, save_cart
from .forms import AddressForm, CheckoutForm
from .models import Order, OrderIssue, OrderItem


def _quantity(value, default="1"):
    try:
        result = Decimal(str(value))
        return max(Decimal("0.25"), min(result, Decimal("99")))
    except (InvalidOperation, TypeError):
        return Decimal(default)


@require_POST
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id, is_available=True)
    cart = get_cart(request)
    key = str(product.id)
    current = Decimal(str(cart.get(key, {}).get("quantity", 0)))
    cart[key] = {**cart.get(key, {}), "quantity": str(current + _quantity(request.POST.get("quantity", 1)))}
    save_cart(request, cart)
    messages.success(request, f"{product.name} se agregó a tu lista.")
    return redirect(request.POST.get("next") or "catalog")


@require_POST
def update_cart(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = get_cart(request)
    key = str(product.id)
    action = request.POST.get("action")
    if action == "remove":
        cart.pop(key, None)
    else:
        current = Decimal(str(cart.get(key, {}).get("quantity", 1)))
        quantity = current + (Decimal("1") if action == "increase" else Decimal("-1"))
        if quantity <= 0:
            cart.pop(key, None)
        else:
            cart[key] = {**cart.get(key, {}), "quantity": str(quantity)}
    save_cart(request, cart)
    return redirect("cart")


def cart_view(request):
    entries, total = cart_entries(request)
    return render(request, "orders/cart.html", {
        "entries": entries,
        "total": total,
        "minimum_total": MINIMUM_ORDER_TOTAL,
        "minimum_reached": total >= MINIMUM_ORDER_TOTAL,
        "minimum_remaining": max(Decimal("0"), MINIMUM_ORDER_TOTAL - total),
        "service_fee": SERVICE_FEE,
        "delivery_fee": DELIVERY_FEE,
        "grand_total": total + SERVICE_FEE + DELIVERY_FEE,
    })


def preferences(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    cart = get_cart(request)
    key = str(product.id)
    if key not in cart:
        cart[key] = {"quantity": "1"}
    if request.method == "POST":
        cart[key]["preferences"] = {
            "freshness": request.POST.get("freshness", "Sin preferencia"),
            "size": request.POST.get("size", "Sin preferencia"),
            "quality": request.POST.get("quality", "Equilibrado"),
            "substitution": request.POST.get("substitution", "Aceptar similar"),
            "tolerance": request.POST.get("tolerance", "10%"),
            "note": request.POST.get("note", "").strip()[:500],
        }
        cart[key]["quantity"] = str(_quantity(request.POST.get("quantity", cart[key].get("quantity", 1))))
        save_cart(request, cart)
        messages.success(request, "Guardamos tus preferencias.")
        return redirect("cart")
    return render(request, "orders/preferences.html", {"product": product, "item": cart[key]})


def address_create(request):
    if not request.session.session_key:
        request.session.create()
    next_name = request.POST.get("next") or request.GET.get("next") or "catalog"
    if next_name not in ("catalog", "checkout"):
        next_name = "catalog"
    form = AddressForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        address = form.save(commit=False)
        address.user = request.user if request.user.is_authenticated else None
        address.session_key = request.session.session_key
        address.save()
        request.session["selected_address_id"] = address.id
        messages.success(request, "Guardamos y seleccionamos tu ubicación de entrega.")
        return redirect(next_name)
    return render(request, "orders/address_form.html", {"form": form, "next_name": next_name})


@transaction.atomic
def checkout(request):
    entries, total = cart_entries(request)
    if not entries:
        messages.info(request, "Agrega al menos un producto antes de continuar.")
        return redirect("catalog")
    if total < MINIMUM_ORDER_TOTAL:
        remaining = MINIMUM_ORDER_TOTAL - total
        messages.error(
            request,
            f"El mínimo de compra es Bs {MINIMUM_ORDER_TOTAL:.2f}. Te faltan Bs {remaining:.2f}.",
        )
        return redirect("cart")
    initial = {"scheduled_date": date.today() + timedelta(days=1), "scheduled_window": "10:00 - 12:00"}
    selected_address_id = request.session.get("selected_address_id")
    if selected_address_id:
        initial["address"] = selected_address_id
    form = CheckoutForm(request.POST or None, initial=initial, request=request)
    if request.method == "POST" and form.is_valid():
        order = Order.objects.create(
            customer=request.user if request.user.is_authenticated else None,
            guest_name=form.cleaned_data["guest_name"],
            address=form.cleaned_data["address"],
            scheduled_date=form.cleaned_data["scheduled_date"],
            scheduled_window=form.cleaned_data["scheduled_window"],
            estimated_total=total + SERVICE_FEE + DELIVERY_FEE,
            service_fee=SERVICE_FEE,
            delivery_fee=DELIVERY_FEE,
        )
        for entry in entries:
            OrderItem.objects.create(
                order=order, product=entry["product"], quantity=entry["quantity"],
                estimated_unit_price=entry["product"].estimated_price,
                preferences=entry["preferences"],
            )
        save_cart(request, {})
        request.session["order_ids"] = request.session.get("order_ids", []) + [order.id]
        messages.success(request, "¡Recibimos tu lista!")
        return redirect("order_detail", pk=order.pk)
    return render(request, "orders/checkout.html", {
        "form": form,
        "entries": entries,
        "total": total,
        "service_fee": SERVICE_FEE,
        "delivery_fee": DELIVERY_FEE,
        "grand_total": total + SERVICE_FEE + DELIVERY_FEE,
        "min_date": date.today().isoformat(),
    })


def _visible_orders(request):
    qs = Order.objects.prefetch_related("items__product")
    if request.user.is_authenticated:
        return qs.filter(customer=request.user)
    return qs.filter(id__in=request.session.get("order_ids", []))


def order_history(request):
    return render(request, "orders/history.html", {"orders": _visible_orders(request)})


def order_detail(request, pk):
    order = get_object_or_404(_visible_orders(request).prefetch_related("items__issues"), pk=pk)
    status_keys = [key for key, _ in Order.STATUS_CHOICES if key != "CANCELLED"]
    current_index = status_keys.index(order.status) if order.status in status_keys else -1
    compact_steps = [
        ("CONFIRMED", "Pedido confirmado", "Tu lista está segura"),
        ("BUYER_ASSIGNED", "Comprador asignado", "Un experto del Abasto prepara tu compra"),
        ("SHOPPING", "Comprando", "Seleccionando tus productos"),
        ("AT_BUFFER", "Preparando pedido", "Revisando y organizando todo"),
        ("OUT_FOR_DELIVERY", "En camino", "Tu compra va hacia ti"),
        ("DELIVERED", "Entregado", "¡Tu mercado llegó!"),
    ]
    step_indexes = {key: status_keys.index(key) for key, _, _ in compact_steps}
    timeline = [{"key": k, "label": l, "detail": d, "done": current_index >= step_indexes[k], "active": current_index == step_indexes[k]} for k, l, d in compact_steps]
    pending_issues = OrderIssue.objects.filter(order_item__order=order, status="PENDING").select_related("order_item__product")
    return render(request, "orders/detail.html", {"order": order, "timeline": timeline, "pending_issues": pending_issues})


@require_POST
@transaction.atomic
def respond_issue(request, pk, issue_id):
    order = get_object_or_404(_visible_orders(request), pk=pk)
    issue = get_object_or_404(OrderIssue, pk=issue_id, order_item__order=order, status="PENDING")
    decision = request.POST.get("decision")
    if decision not in ("accept", "reject"):
        return HttpResponseBadRequest("Decisión inválida")
    issue.status = "ACCEPTED" if decision == "accept" else "REJECTED"
    issue.resolved_at = timezone.now()
    issue.save(update_fields=("status", "resolved_at"))
    if decision == "accept":
        if issue.proposed_price is not None:
            issue.order_item.final_unit_price = issue.proposed_price
        if issue.type == "SUBSTITUTION":
            issue.order_item.status = "SUBSTITUTED"
        issue.order_item.save()
    else:
        issue.order_item.status = "NOT_PURCHASED"
        issue.order_item.save(update_fields=("status",))
    if not OrderIssue.objects.filter(order_item__order=order, status="PENDING").exists() and order.status == "WAITING_CUSTOMER_APPROVAL":
        order.status = "SHOPPING"
        order.save(update_fields=("status",))
    messages.success(request, "Registramos tu respuesta.")
    return redirect("order_detail", pk=order.pk)
