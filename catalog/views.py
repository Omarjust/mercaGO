from django.db.models import Q
from django.shortcuts import render
from .models import Category, Market, Product


def catalog_home(request):
    products = Product.objects.filter(is_available=True).select_related("category", "market")
    categories = Category.objects.all()
    category_slug = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()
    if category_slug:
        products = products.filter(category__slug=category_slug)
    if query:
        products = products.filter(Q(name__icontains=query) | Q(category__name__icontains=query))
    return render(request, "catalog/catalog.html", {
        "market": Market.objects.filter(is_available=True).first(),
        "products": products,
        "categories": categories,
        "active_category": category_slug,
        "query": query,
    })
