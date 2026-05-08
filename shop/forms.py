from django import forms
from django.utils.translation import gettext_lazy as _

from .models import CatalogueItem, Customer, Delivery, Order, OrderItem


class OrderAdminForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = self.fields["customer"].queryset.order_by(
            "first_name", "last_name"
        )
        if "total_price" in self.fields:
            self.fields["total_price"].help_text = (
                "Auto-calculated from order items. You can override if needed."
            )
        if "deposit_paid" in self.fields:
            self.fields["deposit_paid"].help_text = _(
                "When payment rows exist under Payment history on this page, totals are summed from payments "
                "and deposit / payment status become read-only."
            )


class OrderItemInlineForm(forms.ModelForm):
    STATUS_CHOICES = (
        ("pending", "Pending"),
        ("in_production", "In Production"),
        ("completed", "Completed"),
    )

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False, initial="pending")

    class Meta:
        model = OrderItem
        fields = "__all__"
        help_texts = {
            "catalogue_item": "Select a service — garment type and base price fill automatically.",
            "final_price": "Auto-filled from catalogue price × quantity. You can override it.",
            "unit_price": "Base price per unit. Auto-filled from catalogue.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ci_field = self.fields.get("catalogue_item")
        if ci_field:
            ci_field.queryset = CatalogueItem.objects.order_by("name")
            ci_field.label_from_instance = (
                lambda obj: f"{obj.name}  —  ${obj.base_price}"
            )
            ci_field.required = False
        # Hide the legacy catalogue field if present
        if "catalogue" in self.fields:
            self.fields["catalogue"].required = False
            self.fields["catalogue"].widget = forms.HiddenInput()


class OrderWizardForm(forms.Form):
    customer = forms.ModelChoiceField(
        queryset=Customer.objects.none(),
        required=False,
        empty_label="— Select existing customer —",
    )
    create_new_customer = forms.BooleanField(required=False, label="Create new customer instead")
    first_name = forms.CharField(required=False, max_length=100, label="First name")
    last_name = forms.CharField(required=False, max_length=100, label="Last name")
    phone = forms.CharField(required=False, max_length=30)
    email = forms.EmailField(required=False)
    address = forms.CharField(required=False, max_length=255)
    customer_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    due_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    order_notes = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))
    delivery_method = forms.ChoiceField(
        required=False,
        choices=[("pickup", "In-store pickup"), ("home_delivery", "Home delivery")]
    )
    recipient_name = forms.CharField(required=False, max_length=100)
    delivery_address = forms.CharField(required=False, max_length=255)

    deposit_amount = forms.DecimalField(
        required=False, min_value=0, decimal_places=2, max_digits=10, initial=0
    )
    deposit_method = forms.ChoiceField(
        required=False,
        choices=[("cash", "Cash"), ("card", "Card"), ("transfer", "Bank Transfer")]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["customer"].queryset = Customer.objects.order_by("first_name", "last_name")

    def clean(self):
        cleaned_data = super().clean()
        has_customer = bool(cleaned_data.get("customer"))
        create_new = bool(cleaned_data.get("create_new_customer"))

        if not has_customer and not create_new:
            raise forms.ValidationError("Select an existing customer or create a new one.")

        if create_new:
            if not cleaned_data.get("first_name") or not cleaned_data.get("last_name"):
                raise forms.ValidationError("First and last name are required for a new customer.")

        return cleaned_data
