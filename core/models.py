from django.conf import settings
from django.db import models


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True)
    label = models.CharField(max_length=60)
    address = models.CharField(max_length=240)
    reference = models.CharField(max_length=240, blank=True)
    session_key = models.CharField(max_length=40, blank=True, db_index=True, editable=False)

    class Meta:
        verbose_name = "Dirección"
        verbose_name_plural = "Direcciones"

    def __str__(self):
        return f"{self.label} · {self.address}"
