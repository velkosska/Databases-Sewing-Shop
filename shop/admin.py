from decimal import Decimal
import json

from django.contrib import admin, messages
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Q, Sum, Value
from django.db.models.functions import Coalesce, Greatest
from django.http import HttpResponseRedirect
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .forms import OrderAdminForm, OrderItemInlineForm
from .payment_sync import sync_order_payment_totals
from .production_logging import format_order_production_log_summary
from .models import (
    Catalogue,
    CatalogueItem,
    Customer,
    Delivery,
    Employee,
    Material,
    Measurement,
    Order,
    OrderItem,
    OrderItemMaterial,
    OrderItemMeasurement,
    OrderPayment,
    OrderProductionLog,
    ProductionStage,
    WorkTicket,
)

# ── Status label translation maps (used in badge methods) ────────────────────

_ORDER_STATUS = {
    "pending":       _("Pending"),
    "in_production": _("In Production"),
    "completed":     _("Completed"),
    "delivered":     _("Delivered"),
}

_PAYMENT_STATUS = {
    "unpaid":   _("Unpaid"),
    "deposit":  _("Deposit Paid"),
    "paid":     _("Fully Paid"),
}

_TICKET_STATUS = {
    "pending":     _("Pending"),
    "in_progress": _("In Progress"),
    "done":        _("Done"),
}

_PRIORITY = {
    "low":    _("Low"),
    "normal": _("Normal"),
    "high":   _("High"),
    "urgent": _("Urgent"),
}

_ITEM_STATUS = {
    "pending":       _("Pending"),
    "in_production": _("In Production"),
    "completed":     _("Completed"),
}


class BalanceDueFilter(admin.SimpleListFilter):
    title = _("Balance due")
    parameter_name = "balance_filter"

    def lookups(self, request, model_admin):
        return (
            ("owed", _("Has balance owed")),
            ("open", _("Outstanding (not delivered)")),
            ("clear", _("Paid up")),
        )

    def queryset(self, request, queryset):
        v = self.value()
        zero = Value(0, output_field=DecimalField(max_digits=12, decimal_places=2))
        due = Greatest(
            ExpressionWrapper(
                Coalesce(F("total_price"), zero) - Coalesce(F("deposit_paid"), zero),
                output_field=DecimalField(max_digits=14, decimal_places=4),
            ),
            zero,
            output_field=DecimalField(max_digits=14, decimal_places=4),
        )
        queryset = queryset.annotate(_due=due)
        if v == "owed":
            return queryset.filter(_due__gt=0)
        if v == "open":
            return queryset.filter(_due__gt=0).exclude(status=Order.Status.DELIVERED)
        if v == "clear":
            return queryset.filter(_due__lte=0)
        return queryset


# ─── Inlines ────────────────────────────────────────────────────────────────

class OrderItemMaterialInline(TabularInline):
    model = OrderItemMaterial
    extra = 0
    autocomplete_fields = ["material"]
    fields = ["material", "quantity_used", "notes"]
    verbose_name = _("Material used")
    verbose_name_plural = _("Materials used")


class OrderItemMeasurementInline(TabularInline):
    model = OrderItemMeasurement
    extra = 0
    fields = ["bust", "waist", "hips", "shoulder", "sleeve", "length", "inseam", "neck", "notes"]
    verbose_name = _("Measurement")
    verbose_name_plural = _("Measurements")
    can_delete = False


class OrderItemInline(TabularInline):
    model = OrderItem
    form = OrderItemInlineForm
    extra = 1
    fields = [
        "catalogue_item", "garment_type", "color", "quantity",
        "unit_price", "final_price", "assigned_employee", "status",
    ]
    show_change_link = True
    verbose_name = _("Order item")
    verbose_name_plural = _("Order items")


class OrderPaymentInline(TabularInline):
    model = OrderPayment
    extra = 1
    fields = ("recorded_at", "amount", "method", "notes")
    verbose_name = _("Payment")
    verbose_name_plural = _("Payment history")

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("-recorded_at")


class ProductionStageInline(TabularInline):
    model = ProductionStage
    extra = 1
    fields = ["stage_name", "started_at", "completed_at", "comments"]


class DeliveryInline(StackedInline):
    model = Delivery
    extra = 0
    can_delete = False
    fields = ["delivery_method", "recipient_name", "delivered_at", "delivered", "comments"]


class OrderProductionLogInline(TabularInline):
    model = OrderProductionLog
    extra = 0
    max_num = 0
    can_delete = False
    fields = ("created_at", "summary_display")
    readonly_fields = ("created_at", "summary_display")
    verbose_name = _("Production event")
    verbose_name_plural = _("Production log")

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).order_by("-created_at")

    @admin.display(description=_("What happened"))
    def summary_display(self, obj):
        return format_order_production_log_summary(obj)


# ─── Admin Actions ───────────────────────────────────────────────────────────

@admin.action(description=_("Mark selected orders as In Production"))
def mark_in_production(modeladmin, request, queryset):
    updated = 0
    for order in queryset.exclude(status=Order.Status.DELIVERED):
        if order.status != Order.Status.IN_PRODUCTION:
            order.status = Order.Status.IN_PRODUCTION
            order.save(update_fields=["status"])
            updated += 1
    messages.success(request, ngettext(
        "%(count)d order marked as In Production.",
        "%(count)d orders marked as In Production.",
        updated,
    ) % {"count": updated})


@admin.action(description=_("Mark selected orders as Completed"))
def mark_completed(modeladmin, request, queryset):
    updated = 0
    for order in queryset:
        if order.status != Order.Status.COMPLETED:
            order.status = Order.Status.COMPLETED
            order.save(update_fields=["status"])
            updated += 1
    messages.success(request, ngettext(
        "%(count)d order marked as Completed.",
        "%(count)d orders marked as Completed.",
        updated,
    ) % {"count": updated})


@admin.action(description=_("Mark selected orders as Delivered"))
def mark_delivered(modeladmin, request, queryset):
    now = timezone.now()
    count = 0
    for order in queryset.select_related("customer"):
        order.refresh_from_db()
        tp = order.total_price or Decimal("0")
        qp = OrderPayment.objects.filter(order_id=order.pk)
        if qp.exists():
            paid_agg = qp.aggregate(s=Sum("amount"))["s"]
            paid = paid_agg.quantize(Decimal("0.01")) if paid_agg is not None else Decimal("0")
        else:
            paid = (order.deposit_paid or Decimal("0")).quantize(Decimal("0.01"))

        balance = (tp - paid).quantize(Decimal("0.01"))
        if balance > Decimal("0"):
            OrderPayment.objects.create(
                order=order,
                amount=balance,
                method=OrderPayment.Method.ADMIN_MARK_DELIVERED,
                notes=str(_("Captured on mark delivered (admin)")),
            )

        order.status = Order.Status.DELIVERED
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=["status", "payment_status"])
        delivery, created = Delivery.objects.get_or_create(
            order=order,
            defaults={
                "delivered": True,
                "delivered_at": now,
                "recipient_name": order.customer.full_name,
                "delivery_method": Delivery.Method.PICKUP,
            },
        )
        if not created:
            delivery.delivered = True
            delivery.delivered_at = now
            if not delivery.recipient_name:
                delivery.recipient_name = order.customer.full_name
            if not delivery.delivery_method:
                delivery.delivery_method = Delivery.Method.PICKUP
            delivery.save(update_fields=[
                "delivered", "delivered_at", "recipient_name", "delivery_method",
            ])
        count += 1
    messages.success(request, ngettext(
        "%(count)d order marked as Delivered.",
        "%(count)d orders marked as Delivered.",
        count,
    ) % {"count": count})


@admin.action(description=_("Mark selected work tickets as In Progress"))
def ticket_in_progress(modeladmin, request, queryset):
    for ticket in queryset:
        if ticket.status != WorkTicket.Status.IN_PROGRESS:
            ticket.status = WorkTicket.Status.IN_PROGRESS
            ticket.save(update_fields=["status"])


@admin.action(description=_("Mark selected work tickets as Done"))
def ticket_done(modeladmin, request, queryset):
    for ticket in queryset:
        if ticket.status != WorkTicket.Status.DONE:
            ticket.status = WorkTicket.Status.DONE
            ticket.save(update_fields=["status"])


# ─── Customer ────────────────────────────────────────────────────────────────

@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ["full_name_display", "phone", "email", "order_count", "created_at"]
    search_fields = ["first_name", "last_name", "phone", "email"]
    list_filter = ["created_at"]
    fieldsets = (
        (_("Contact Information"), {
            "fields": (("first_name", "last_name"), ("phone", "email"), "address")
        }),
        (_("Notes"), {"fields": ("notes",), "classes": ("collapse",)}),
    )

    @admin.display(description=_("Customer"))
    def full_name_display(self, obj):
        return obj.full_name

    @admin.display(description=_("Orders"))
    def order_count(self, obj):
        count = obj.orders.count()
        if count == 0:
            return format_html('<span style="color:#9ca3af">{}</span>', _("No orders"))
        url = f"/admin/shop/order/?customer__id__exact={obj.pk}"
        label = ngettext("%(n)d order", "%(n)d orders", count) % {"n": count}
        return format_html('<a href="{}">{}</a>', url, label)


# ─── Employee ────────────────────────────────────────────────────────────────

@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = ["full_name_display", "role", "phone", "active_tickets"]
    search_fields = ["first_name", "last_name", "role"]
    list_filter = ["role"]
    fieldsets = (
        (_("Employee Details"), {"fields": (("first_name", "last_name"), "role", "phone")}),
        (_("Notes"), {"fields": ("notes",), "classes": ("collapse",)}),
    )

    @admin.display(description=_("Employee"))
    def full_name_display(self, obj):
        return obj.full_name

    @admin.display(description=_("Active Tickets"))
    def active_tickets(self, obj):
        count = obj.tickets.exclude(status=WorkTicket.Status.DONE).count()
        if count == 0:
            return format_html('<span style="color:#9ca3af">{}</span>', _("None"))
        return format_html('<strong style="color:#d97706">{}</strong>', count)


# ─── Material ────────────────────────────────────────────────────────────────

@admin.register(Material)
class MaterialAdmin(ModelAdmin):
    list_display = ["name", "color", "unit_price", "stock_quantity", "stock_status", "supplier"]
    search_fields = ["name", "color", "supplier"]
    list_filter = ["color"]
    fieldsets = (
        (_("Material Details"), {
            "fields": (("name", "color"), ("unit_price", "stock_quantity"))
        }),
        (_("Stock Alerts & Supplier"), {
            "fields": ("low_stock_threshold", "supplier"),
            "description": _("Set a threshold to get low-stock alerts on the dashboard.")
        }),
    )

    @admin.display(description=_("Stock Status"))
    def stock_status(self, obj):
        if obj.stock_quantity is None:
            return format_html('<span style="color:#9ca3af">{}</span>', _("Not tracked"))
        if obj.is_low_stock:
            return format_html(
                '<span style="color:#dc2626; font-weight:600">⚠ {} ({} {})</span>',
                _("Low"), obj.stock_quantity, _("units")
            )
        return mark_safe('<span style="color:#16a34a">✓ OK</span>')


# ─── Catalogue ───────────────────────────────────────────────────────────────

@admin.register(Catalogue)
class CatalogueAdmin(ModelAdmin):
    list_display = ["service", "base_price"]
    search_fields = ["service"]


@admin.register(CatalogueItem)
class CatalogueItemAdmin(ModelAdmin):
    list_display = ["name", "base_price", "price_hint", "garment_count", "requires_measurements"]
    search_fields = ["name"]
    list_filter = ["requires_measurements"]
    fieldsets = (
        (_("Service Details"), {
            "fields": ("name", "garment_types", "base_price", "price_hint")
        }),
        (_("Options"), {"fields": ("requires_measurements",)}),
    )

    @admin.display(description=_("Garment Types"))
    def garment_count(self, obj):
        types = obj.garment_types
        if not types:
            return "-"
        return ", ".join(types[:3]) + ("…" if len(types) > 3 else "")


# ─── Order ───────────────────────────────────────────────────────────────────

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    form = OrderAdminForm
    list_display = [
        "order_id", "customer_link", "garment_summary",
        "order_date_display", "due_date_display", "status_badge", "payment_badge",
        "total_display", "balance_due_display",
    ]
    search_fields = ["customer__first_name", "customer__last_name"]
    list_filter = ["status", "payment_status", "order_date", "due_date", BalanceDueFilter]
    ordering = ["-order_date"]
    autocomplete_fields = ["customer"]
    actions = [mark_in_production, mark_completed, mark_delivered]
    inlines = [OrderItemInline, OrderPaymentInline, DeliveryInline, OrderProductionLogInline]
    fieldsets = (
        (_("Order Information"), {
            "fields": ("customer", ("due_date", "status"), "notes"),
        }),
        (_("Pricing & Payment"), {
            "fields": (("total_price", "deposit_paid"), "payment_status"),
            "description": _(
                "Total price is usually the sum of line items. When payment history lines exist, "
                "paid total and payment status are recalculated from those lines."
            ),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        ro = list(super().get_readonly_fields(request, obj))
        if obj is not None and obj.payments.exists():
            for f in ("deposit_paid", "payment_status"):
                if f not in ro:
                    ro.append(f)
        return ro

    def get_search_results(self, request, queryset, search_term):
        """Numeric terms match primary key (avoid id__icontains on integer FK)."""
        queryset, duplicates = super().get_search_results(request, queryset, search_term)
        if search_term:
            stripped = search_term.strip()
            if stripped.isdigit():
                try:
                    queryset = queryset | self.model.objects.filter(pk=int(stripped))
                    duplicates = True
                except (ValueError, TypeError):
                    pass
            return queryset.distinct(), duplicates
        return queryset, duplicates

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("customer").prefetch_related("items")

    @admin.display(description=_("Order #"))
    def order_id(self, obj):
        return format_html("<strong>#{}</strong>", obj.pk)

    @admin.display(description=_("Customer"))
    def customer_link(self, obj):
        url = f"/admin/shop/customer/{obj.customer_id}/change/"
        return format_html('<a href="{}">{}</a>', url, obj.customer.full_name)

    @admin.display(description=_("Items"))
    def garment_summary(self, obj):
        items = list(obj.items.all()[:3])
        if not items:
            return format_html('<span style="color:#9ca3af">{}</span>', _("No items"))
        labels = []
        for it in items:
            garment = it.garment_type or (it.catalogue_item.name if it.catalogue_item else str(_("Item")))
            labels.append(garment)
        text = ", ".join(labels)
        extra = obj.items.count() - 3
        if extra > 0:
            text += f" +{extra} {_('more')}"
        return text

    @admin.display(description=_("Order date"), ordering="order_date")
    def order_date_display(self, obj):
        return obj.order_date

    @admin.display(description=_("Due Date"))
    def due_date_display(self, obj):
        if not obj.due_date:
            return format_html('<span style="color:#9ca3af">{}</span>', _("Not set"))
        today = timezone.localdate()
        days = (obj.due_date - today).days
        if days < 0 and obj.status not in (Order.Status.COMPLETED, Order.Status.DELIVERED):
            return format_html(
                '<span style="color:#dc2626; font-weight:600">{} <small>({}{})</small></span>',
                obj.due_date, abs(days), _("d overdue")
            )
        if 0 <= days <= 3 and obj.status not in (Order.Status.COMPLETED, Order.Status.DELIVERED):
            return format_html(
                '<span style="color:#d97706; font-weight:600">{} <small>({}{})</small></span>',
                obj.due_date, days, _("d left")
            )
        return format_html("{}", obj.due_date)

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "pending":       ("#92400e", "#fef3c7"),
            "in_production": ("#1d4ed8", "#dbeafe"),
            "completed":     ("#166534", "#dcfce7"),
            "delivered":     ("#115e59", "#ccfbf1"),
        }
        fg, bg = colors.get(obj.status, ("#374151", "#e5e7eb"))
        label = _ORDER_STATUS.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600">{}</span>',
            bg, fg, label
        )

    @admin.display(description=_("Payment"))
    def payment_badge(self, obj):
        colors = {
            "unpaid":  ("#991b1b", "#fee2e2"),
            "deposit": ("#92400e", "#fef3c7"),
            "paid":    ("#166534", "#dcfce7"),
        }
        fg, bg = colors.get(obj.payment_status, ("#374151", "#e5e7eb"))
        label = _PAYMENT_STATUS.get(obj.payment_status, obj.payment_status)
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:999px;font-size:12px">{}</span>',
            bg, fg, label
        )

    @admin.display(description=_("Total"))
    def total_display(self, obj):
        if obj.total_price is None:
            return mark_safe('<span style="color:#9ca3af">—</span>')
        return format_html("<strong>${}</strong>", obj.total_price)

    @admin.display(description=_("Balance due"))
    def balance_due_display(self, obj):
        if obj.total_price is None:
            return mark_safe('<span style="color:#9ca3af">—</span>')
        d = obj.balance_due
        if d <= 0:
            return mark_safe('<span style="color:#16a34a;font-weight:600">$0</span>')
        return format_html('<span style="color:#b45309;font-weight:600">${}</span>', d)

    def add_view(self, request, form_url="", extra_context=None):
        """Send the admin user to the polished Next.js wizard instead of the raw form."""
        return HttpResponseRedirect("http://localhost:3000/orders/new?from=admin")

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        order = form.instance
        total = order.items.aggregate(total=Sum("final_price")).get("total")
        computed = total if total is not None else Decimal("0.00")
        if order.total_price is None:
            order.total_price = computed
            order.save(update_fields=["total_price"])
        sync_order_payment_totals(order.pk)


@admin.register(OrderPayment)
class OrderPaymentAdmin(ModelAdmin):
    list_display = [
        "recorded_at",
        "order_link",
        "customer_display",
        "amount_display",
        "method_display",
        "balance_hint",
        "notes",
    ]
    list_filter = ["method", "recorded_at"]
    search_fields = [
        "notes",
        "order__customer__first_name",
        "order__customer__last_name",
        "order__pk",
    ]
    autocomplete_fields = ["order"]
    ordering = ["-recorded_at"]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order__customer")

    @admin.display(description=_("Order"))
    def order_link(self, obj):
        url = f"/admin/shop/order/{obj.order_id}/change/"
        return format_html('<a href="{}">#{}</a>', url, obj.order_id)

    @admin.display(description=_("Customer"))
    def customer_display(self, obj):
        return obj.order.customer.full_name

    @admin.display(description=_("Amount"))
    def amount_display(self, obj):
        return format_html("<strong>${}</strong>", obj.amount)

    @admin.display(description=_("Method"))
    def method_display(self, obj):
        return dict(OrderPayment.Method.choices).get(obj.method, obj.method)

    @admin.display(description=_("Remaining on order"))
    def balance_hint(self, obj):
        o = obj.order
        remain = o.balance_due if o.pk else Decimal("0")
        if remain <= 0:
            return format_html('<span style="color:#16a34a;font-weight:600">$0 · {}</span>', _("Paid up"))
        return format_html('<span style="color:#b45309;font-weight:600">${} {}</span>', remain, _("owed"))


# ─── Order Item ───────────────────────────────────────────────────────────────

@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    form = OrderItemInlineForm
    list_display = [
        "id", "order_link", "catalogue_item", "garment_type",
        "quantity", "unit_price", "final_price", "status_badge", "assigned_employee",
    ]
    search_fields = [
        "garment_type", "catalogue_item__name",
        "order__customer__first_name", "order__customer__last_name",
    ]
    list_filter = ["status", "catalogue_item"]
    autocomplete_fields = ["order", "catalogue_item"]
    inlines = [OrderItemMeasurementInline, OrderItemMaterialInline]
    fieldsets = (
        (_("Item Details"), {
            "fields": (
                ("order", "catalogue_item"),
                ("garment_type", "color"),
                ("quantity", "unit_price", "final_price"),
                "price_overridden",
            )
        }),
        (_("Assignment"), {
            "fields": ("assigned_employee", "status"),
        }),
        (_("Notes & Design"), {
            "fields": ("design_notes", "item_notes", "color_fabric"),
            "classes": ("collapse",),
        }),
    )

    class Media:
        js = ("shop/admin/order_flow.js",)
        css = {"all": ("shop/admin/order_flow.css",)}

    @admin.display(description=_("Order"))
    def order_link(self, obj):
        url = f"/admin/shop/order/{obj.order_id}/change/"
        return format_html('<a href="{}">#{} — {}</a>', url, obj.order_id, obj.order.customer.full_name)

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "pending":       ("#92400e", "#fef3c7"),
            "in_production": ("#1d4ed8", "#dbeafe"),
            "completed":     ("#166534", "#dcfce7"),
        }
        fg, bg = colors.get(obj.status, ("#374151", "#e5e7eb"))
        label = _ITEM_STATUS.get(obj.status, obj.status.replace("_", " ").title())
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:999px;font-size:12px">{}</span>',
            bg, fg, label
        )


# ─── Measurement ─────────────────────────────────────────────────────────────

@admin.register(Measurement)
class MeasurementAdmin(ModelAdmin):
    list_display = ["customer", "chest", "waist", "hip", "shoulder", "sleeve_length", "inseam", "updated_at"]
    search_fields = ["customer__first_name", "customer__last_name"]
    autocomplete_fields = ["customer"]


# ─── Work Ticket ─────────────────────────────────────────────────────────────

@admin.register(WorkTicket)
class WorkTicketAdmin(ModelAdmin):
    list_display = [
        "ticket_id", "order_customer", "garment_display", "assigned_to",
        "priority_badge", "status_badge", "deadline_display", "created_at",
    ]
    search_fields = [
        "order_item__garment_type", "assigned_to__first_name",
        "assigned_to__last_name", "order_item__order__customer__first_name",
    ]
    list_filter = ["status", "priority", "deadline"]
    autocomplete_fields = ["assigned_to"]
    actions = [ticket_in_progress, ticket_done]
    inlines = [ProductionStageInline]
    fieldsets = (
        (_("Ticket Details"), {
            "fields": ("order_item", ("assigned_to", "priority"), ("status", "deadline"))
        }),
        (_("Notes"), {"fields": ("notes",), "classes": ("collapse",)}),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related("order_item__order__customer", "assigned_to")

    @admin.display(description=_("Ticket"))
    def ticket_id(self, obj):
        return format_html("<strong>#{}</strong>", obj.pk)

    @admin.display(description=_("Customer"))
    def order_customer(self, obj):
        return obj.order_item.order.customer.full_name

    @admin.display(description=_("Garment"))
    def garment_display(self, obj):
        return obj.order_item.garment_type or "—"

    @admin.display(description=_("Priority"))
    def priority_badge(self, obj):
        colors = {
            "urgent": ("#991b1b", "#fee2e2"),
            "high":   ("#92400e", "#fef3c7"),
            "normal": ("#1d4ed8", "#dbeafe"),
            "low":    ("#374151", "#e5e7eb"),
        }
        fg, bg = colors.get(obj.priority, ("#374151", "#e5e7eb"))
        label = _PRIORITY.get(obj.priority, obj.get_priority_display())
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:999px;font-size:12px;font-weight:600">{}</span>',
            bg, fg, label
        )

    @admin.display(description=_("Status"))
    def status_badge(self, obj):
        colors = {
            "pending":     ("#92400e", "#fef3c7"),
            "in_progress": ("#1d4ed8", "#dbeafe"),
            "done":        ("#166534", "#dcfce7"),
        }
        fg, bg = colors.get(obj.status, ("#374151", "#e5e7eb"))
        label = _TICKET_STATUS.get(obj.status, obj.get_status_display())
        return format_html(
            '<span style="background:{};color:{};padding:2px 8px;border-radius:999px;font-size:12px">{}</span>',
            bg, fg, label
        )

    @admin.display(description=_("Deadline"))
    def deadline_display(self, obj):
        if not obj.deadline:
            return format_html('<span style="color:#9ca3af">{}</span>', _("Not set"))
        today = timezone.localdate()
        days = (obj.deadline - today).days
        if days < 0 and obj.status != WorkTicket.Status.DONE:
            return format_html(
                '<span style="color:#dc2626; font-weight:600">{} <small>({}{})</small></span>',
                obj.deadline, abs(days), _("d overdue")
            )
        if 0 <= days <= 2 and obj.status != WorkTicket.Status.DONE:
            return format_html(
                '<span style="color:#d97706; font-weight:600">{} <small>({}{})</small></span>',
                obj.deadline, days, _("d left")
            )
        return format_html("{}", obj.deadline)


# ─── Production Stage ────────────────────────────────────────────────────────

@admin.register(ProductionStage)
class ProductionStageAdmin(ModelAdmin):
    list_display = ["work_ticket", "stage_name", "started_at", "completed_at"]
    search_fields = ["work_ticket__id", "stage_name"]
    list_filter = ["stage_name"]


# ─── Delivery ────────────────────────────────────────────────────────────────

@admin.register(Delivery)
class DeliveryAdmin(ModelAdmin):
    list_display = ["order_display", "delivery_method", "recipient_name", "delivered_at", "delivered_badge"]
    search_fields = [
        "order__customer__first_name", "order__customer__last_name", "recipient_name"
    ]
    list_filter = ["delivered", "delivery_method", "delivered_at"]
    autocomplete_fields = ["order"]
    fieldsets = (
        (_("Delivery Details"), {
            "fields": ("order", ("delivery_method", "recipient_name"), ("delivered_at", "delivered"))
        }),
        (_("Comments"), {"fields": ("comments",), "classes": ("collapse",)}),
    )

    @admin.display(description=_("Order"))
    def order_display(self, obj):
        return format_html(
            '<a href="/admin/shop/order/{}/change/">#{} — {}</a>',
            obj.order_id, obj.order_id, obj.order.customer.full_name
        )

    @admin.display(description=_("Delivered?"))
    def delivered_badge(self, obj):
        if obj.delivered:
            return format_html(
                '<span style="color:#16a34a; font-weight:600">✓ {}</span>', _("Delivered")
            )
        return format_html('<span style="color:#9ca3af">{}</span>', _("Pending"))


# ─── Production log (read-only timeline) ───────────────────────────────────────

@admin.register(OrderProductionLog)
class OrderProductionLogAdmin(ModelAdmin):
    list_display = ["created_at", "order_link", "kind_display", "summary_short"]
    list_filter = ["kind", "created_at"]
    search_fields = [
        "order__id",
        "order__customer__first_name",
        "order__customer__last_name",
    ]
    ordering = ["-created_at"]
    readonly_fields = ("created_at", "order", "kind", "payload_display", "summary_short")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("order__customer")

    @admin.display(description=_("Order"))
    def order_link(self, obj):
        url = f"/admin/shop/order/{obj.order_id}/change/"
        return format_html(
            '<a href="{}">#{} — {}</a>',
            url,
            obj.order_id,
            obj.order.customer.full_name,
        )

    @admin.display(description=_("Kind"))
    def kind_display(self, obj):
        label = dict(OrderProductionLog.Kind.choices).get(obj.kind, obj.kind)
        return str(label)

    @admin.display(description=_("Payload"))
    def payload_display(self, obj):
        text = json.dumps(obj.payload or {}, indent=2, sort_keys=True, ensure_ascii=True)
        return format_html('<pre style="margin:0;white-space:pre-wrap;font-size:12px">{}</pre>', text)

    @admin.display(description=_("Summary"))
    def summary_short(self, obj):
        return format_order_production_log_summary(obj)
