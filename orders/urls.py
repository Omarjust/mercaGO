from django.urls import path
from . import views

urlpatterns = [
    path("lista/", views.cart_view, name="cart"),
    path("lista/agregar/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("lista/actualizar/<int:product_id>/", views.update_cart, name="update_cart"),
    path("lista/preferencias/<int:product_id>/", views.preferences, name="preferences"),
    path("ubicaciones/nueva/", views.address_create, name="address_create"),
    path("confirmar/", views.checkout, name="checkout"),
    path("mis-compras/", views.order_history, name="order_history"),
    path("orders/<int:pk>/", views.order_detail, name="order_detail"),
    path("orders/<int:pk>/incidencias/<int:issue_id>/", views.respond_issue, name="respond_issue"),
]
