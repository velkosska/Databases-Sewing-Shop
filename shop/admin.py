from decimal import Decimal

from django.contrib import admin, messages
from django.db.models import Count, Q, Sum
from django.http import HttpResponseRedirect
from django.utils.html import format_html, mark_safe
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, ngettext
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .forms import OrderAdminForm, OrderItemInlineForm
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


class ProductionStageInline(TabularInline):
    model = ProductionStage
    extra = 1
    fields = ["stage_name", "started_at", "completed_at", "comments"]


class DeliveryInline(StackedInline):
    model = Delivery
    extra = 0
    can_delete = False
    fields = ["delivery_method", "recipient_name", "delivered_at", "delivered", "comments"]


# ─── Admin Actions ───────────────────────────────────────────────────────────

@admin.action(description=_("Mark selected orders as In Production"))
def mark_in_production(modeladmin, request, queryset):
    updated = queryset.exclude(status=Order.Status.DELIVERED).update(status=Order.Status.IN_PRODUCTION)
    messages.success(request, ngettext(
        "%(count)d order marked as In Production.",
        "%(count)d orders marked as In Production.",
        updated,
    ) % {"count": updated})


@admin.action(description=_("Mark selected orders as Completed"))
def mark_completed(modeladmin, request, queryset):
    updated = queryset.update(status=Order.Status.COMPLETED)
    messages.success(request, ngettext(
        "%(count)d order marked as Completed.",
        "%(count)d orders marked as Completed.",
        updated,
    ) % {"count": updated})


@admin.action(description=_("Mark selected orders as Delivered"))
def mark_delivered(modeladmin, request, queryset):
    now = timezone.now()
    count = 0
    for order in queryset:
        order.status = Order.Status.DELIVERED
        order.payment_status = Order.PaymentStatus.PAID
        order.save(update_fields=["status", "payment_status"])
        Delivery.objects.update_or_create(
            order=order,
            defaults={"delivered": True, "delivered_at": now, "recipient_name": order.customer.full_name},
        )
        count += 1
    messages.success(request, ngettext(
        "%(count)d order marked as Delivered.",
        "%(count)d orders marked as Delivered.",
        count,
    ) % {"count": count})


@admin.action(description=_("Mark selected work tickets as In Progress"))
def ticket_in_progress(modeladmin, request, queryset):
    queryset.update(status=WorkTicket.Status.IN_PROGRESS)


@admin.action(description=_("Mark selected work tickets as Done"))
def ticket_done(modeladmin, request, queryset):
    queryset.update(status=WorkTicket.Status.DONE)


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
        "order_date_display", "due_date_display", "status_badge", "payment_badge", "total_display",
    ]
    search_fields = ["customer__first_name", "customer__last_name", "id"]
    list_filter = ["status", "payment_status", "order_date", "due_date"]
    ordering = ["-order_date"]
    autocomplete_fields = ["customer"]
    actions = [mark_in_production, mark_completed, mark_delivered]
    inlines = [OrderItemInline, DeliveryInline]
    fieldsets = (
        (_("Order Information"), {
            "fields": ("customer", ("due_date", "status"), "notes"),
        }),
        (_("Pricing & Payment"), {
            "fields": (("total_price", "deposit_paid"), "payment_status"),
            "description": _("Total price auto-calculates from items. Deposit is recorded at intake."),
        }),
    )

    class Media:
        js = ("shop/admin/order_flow.js",)
        css = {"all": ("shop/admin/order_flow.css",)}

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
