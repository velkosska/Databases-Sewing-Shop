from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class Customer(models.Model):
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(max_length=150, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "customer"
        ordering = ["first_name", "last_name"]
        verbose_name = _("Customer")
        verbose_name_plural = _("Customers")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return self.full_name


class Employee(models.Model):
    first_name = models.CharField(max_length=100, default="")
    last_name = models.CharField(max_length=100, default="")
    role = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "employee"
        ordering = ["first_name", "last_name"]
        verbose_name = _("Employee")
        verbose_name_plural = _("Employees")

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class Material(models.Model):
    name = models.CharField(max_length=150)
    color = models.CharField(max_length=80, blank=True, null=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock_quantity = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    low_stock_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True,
        help_text=_("Alert when stock drops below this quantity.")
    )
    supplier = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = "material"
        ordering = ["name"]
        verbose_name = _("Material")
        verbose_name_plural = _("Materials")

    def __str__(self):
        return f"{self.name} ({self.color})" if self.color else self.name

    @property
    def is_low_stock(self):
        if self.low_stock_threshold is not None and self.stock_quantity is not None:
            return self.stock_quantity <= self.low_stock_threshold
        return False


class Catalogue(models.Model):
    service = models.CharField(max_length=100)
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = "catalogue"
        ordering = ["service"]
        verbose_name = _("Catalogue")
        verbose_name_plural = _("Catalogue")

    def __str__(self):
        return self.service


class CatalogueItem(models.Model):
    name = models.CharField(max_length=200)
    garment_types = models.JSONField(default=list)
    base_price = models.DecimalField(max_digits=8, decimal_places=2)
    price_hint = models.CharField(max_length=200, blank=True)
    requires_measurements = models.BooleanField(default=True)

    class Meta:
        db_table = "catalogue_item"
        ordering = ["name"]
        verbose_name = _("Catalogue Item")
        verbose_name_plural = _("Catalogue Items")

    def __str__(self):
        return f"{self.name}  —  ${self.base_price}"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        IN_PRODUCTION = "in_production", _("In Production")
        COMPLETED = "completed", _("Completed")
        DELIVERED = "delivered", _("Delivered")

    class PaymentStatus(models.TextChoices):
        UNPAID = "unpaid", _("Unpaid")
        DEPOSIT = "deposit", _("Deposit Paid")
        PAID = "paid", _("Fully Paid")

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    order_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    deposit_paid = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text=_("Amount paid as deposit at time of order.")
    )
    payment_status = models.CharField(
        max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.UNPAID
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "orders"
        ordering = ["-order_date"]
        verbose_name = _("Order")
        verbose_name_plural = _("Orders")

    @property
    def balance_due(self):
        total = self.total_price or 0
        return max(total - self.deposit_paid, 0)

    def __str__(self):
        return f"Order #{self.pk} - {self.customer.full_name}"


class OrderPayment(models.Model):
    """Individual payment recording for orders (ledger-style history)."""

    class Method(models.TextChoices):
        CASH = "cash", _("Cash")
        CARD = "card", _("Card")
        TRANSFER = "transfer", _("Bank transfer")
        OTHER = "other", _("Other")
        ADMIN_MARK_DELIVERED = "admin_mark_delivered", _("Marked delivered (admin)")

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=32, choices=Method.choices, default=Method.CASH)
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "order_payment"
        ordering = ["-recorded_at"]
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")

    def __str__(self):
        return f"${self.amount} on order #{self.order_id}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    catalogue = models.ForeignKey(Catalogue, on_delete=models.PROTECT, related_name="order_items", blank=True, null=True)
    catalogue_item = models.ForeignKey("CatalogueItem", null=True, blank=True, on_delete=models.SET_NULL)
    garment_type = models.CharField(max_length=100, blank=True, null=True)
    color_fabric = models.CharField(max_length=200, blank=True)
    unit_price = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    item_notes = models.TextField(blank=True)
    assigned_employee = models.ForeignKey(
        "Employee",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        db_constraint=False,
    )
    price_overridden = models.BooleanField(default=False)
    color = models.CharField(max_length=80, blank=True, null=True)
    design_notes = models.TextField(blank=True, null=True)
    quantity = models.PositiveIntegerField(default=1)
    status = models.CharField(max_length=50, default="pending")
    final_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    materials = models.ManyToManyField(
        Material,
        through="OrderItemMaterial",
        related_name="order_items",
        blank=True,
    )

    class Meta:
        db_table = "order_item"
        verbose_name = _("Order Item")
        verbose_name_plural = _("Order Items")

    def __str__(self):
        return f"{self.garment_type} (Order #{self.order.pk})"


class Measurement(models.Model):
    customer = models.OneToOneField(
        Customer,
        on_delete=models.CASCADE,
        related_name="measurement",
        blank=True,
        null=True,
        db_constraint=False,
    )
    chest = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    waist = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    hip = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    shoulder = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    sleeve_length = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    inseam = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "measurement"
        verbose_name = _("Measurement")
        verbose_name_plural = _("Measurements")

    def __str__(self):
        return f"Measurements for {self.customer.full_name}"


class OrderItemMeasurement(models.Model):
    customer = models.ForeignKey(
        Customer,
        on_delete=models.CASCADE,
        related_name="item_measurements",
        db_constraint=False,
    )
    order_item = models.ForeignKey(
        OrderItem,
        on_delete=models.CASCADE,
        related_name="measurements",
        db_constraint=False,
    )
    bust = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    waist = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    hips = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    shoulder = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    sleeve = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    length = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    inseam = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    neck = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "order_item_measurement"
        ordering = ["-created_at"]
        verbose_name = _("Order Item Measurement")
        verbose_name_plural = _("Order Item Measurements")

    def __str__(self):
        return f"Measurements for item #{self.order_item_id}"


class WorkTicket(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        IN_PROGRESS = "in_progress", _("In Progress")
        DONE = "done", _("Done")

    class Priority(models.TextChoices):
        LOW = "low", _("Low")
        NORMAL = "normal", _("Normal")
        HIGH = "high", _("High")
        URGENT = "urgent", _("Urgent")

    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="ticket")
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets")
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    deadline = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "work_ticket"
        ordering = ["-priority", "deadline"]
        verbose_name = _("Work Ticket")
        verbose_name_plural = _("Work Tickets")

    def __str__(self):
        return f"Ticket #{self.pk} - {self.order_item.garment_type} [{self.priority}]"


class ProductionStage(models.Model):
    class StageName(models.TextChoices):
        ORDER_RECEIVED = "order_received", _("Order Received")
        DESIGN_CONFIRMED = "design_confirmed", _("Design Confirmed")
        CUTTING = "cutting", _("Cutting")
        SEWING = "sewing", _("Sewing")
        FINISHING = "finishing", _("Finishing")
        QUALITY_CHECK = "quality_check", _("Quality Check")
        READY_FOR_DELIVERY = "ready_for_delivery", _("Ready for Delivery")
        DELIVERED = "delivered", _("Delivered")

    work_ticket = models.ForeignKey(WorkTicket, on_delete=models.CASCADE, related_name="stages")
    stage_name = models.CharField(max_length=100, choices=StageName.choices)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "production_stage"
        ordering = ["started_at"]
        verbose_name = _("Production Stage")
        verbose_name_plural = _("Production Stages")

    def __str__(self):
        return f"{self.get_stage_name_display()} - Ticket #{self.work_ticket.pk}"


class Delivery(models.Model):
    class Method(models.TextChoices):
        PICKUP = "pickup", _("Pickup")
        COURIER = "courier", _("Courier")
        IN_STORE = "in_store", _("In Store")

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery")
    delivered_at = models.DateTimeField(blank=True, null=True)
    delivery_method = models.CharField(max_length=50, choices=Method.choices, blank=True, null=True)
    recipient_name = models.CharField(max_length=100, blank=True, null=True)
    delivered = models.BooleanField(default=False)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "delivery"
        ordering = ["-delivered_at"]
        verbose_name = _("Delivery")
        verbose_name_plural = _("Deliveries")

    def __str__(self):
        delivered_status = _("Delivered") if self.delivered else _("Pending")
        return f"Delivery for Order #{self.order.pk} - {delivered_status}"


class OrderProductionLog(models.Model):
    class Kind(models.TextChoices):
        ORDER_STATUS = "order_status", _("Order status")
        PAYMENT_STATUS = "payment_status", _("Payment status")
        ORDER_ITEM_STATUS = "order_item_status", _("Line item status")
        ORDER_ITEM_ASSIGNED = "order_item_assigned", _("Line item assignment")
        TICKET_STATUS = "ticket_status", _("Work ticket status")
        TICKET_ASSIGNED = "ticket_assigned", _("Work ticket assignment")
        STAGE_STARTED = "stage_started", _("Stage started")
        STAGE_COMPLETED = "stage_completed", _("Stage finished")
        DELIVERY = "delivery", _("Delivery")

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="production_logs")
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    kind = models.CharField(max_length=32, choices=Kind.choices)
    payload = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "order_production_log"
        ordering = ["-created_at"]
        verbose_name = _("Production log")
        verbose_name_plural = _("Production logs")

    def __str__(self):
        return f"{self.order_id} {self.kind} @ {self.created_at}"


class OrderItemMaterial(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.RESTRICT)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "order_item_material"
        unique_together = ("order_item", "material")
        verbose_name = _("Order Item Material")
        verbose_name_plural = _("Order Item Materials")

    def __str__(self):
        return f"{self.material.name} for {self.order_item}"
