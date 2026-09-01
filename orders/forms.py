from datetime import date
from django import forms
from django.db.models import Q
from core.models import Address
from .models import Order


class CheckoutForm(forms.Form):
    guest_name = forms.CharField(label="Nombre de quien recibe", max_length=100)
    address = forms.ModelChoiceField(label="Dirección de entrega", queryset=Address.objects.all(), empty_label=None)
    scheduled_date = forms.DateField(label="Fecha", widget=forms.DateInput(attrs={"type": "date"}))
    scheduled_window = forms.ChoiceField(label="Ventana de entrega", choices=Order.WINDOW_CHOICES)

    def __init__(self, *args, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request is not None:
            session_key = request.session.session_key or ""
            allowed = Q(session_key="") | Q(session_key=session_key)
            if request.user.is_authenticated:
                allowed |= Q(user=request.user)
            self.fields["address"].queryset = Address.objects.filter(allowed)

    def clean_scheduled_date(self):
        value = self.cleaned_data["scheduled_date"]
        if value < date.today():
            raise forms.ValidationError("La fecha no puede ser anterior a hoy.")
        return value


class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ("label", "address", "reference")
        labels = {
            "label": "Nombre del lugar",
            "address": "Dirección exacta",
            "reference": "Referencia para encontrarla",
        }
        widgets = {
            "label": forms.TextInput(attrs={"placeholder": "Ej. Casa, trabajo o restaurante"}),
            "address": forms.TextInput(attrs={"placeholder": "Ej. Av. Beni, calle 4, N.º 120"}),
            "reference": forms.Textarea(attrs={"rows": 3, "placeholder": "Ej. Portón negro frente a la farmacia"}),
        }
