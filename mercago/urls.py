from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("mercago/", include("catalog.urls")),
    path("mercago/", include("orders.urls")),
]
