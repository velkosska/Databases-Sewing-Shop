from django.db import models


class Customer(models.Model):
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(max_length=150, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateField(auto_now_add=True)

    class Meta:
        db_table = "customer"
        ordering = ["full_name"]
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

    def __str__(self):
        return self.full_name


class Employee(models.Model):
    full_name = models.CharField(max_length=150)
    role = models.CharField(max_length=100, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    active = models.BooleanField(default=True)

    class Meta:
        db_table = "employee"
        ordering = ["full_name"]
        verbose_name = "Employee"
        verbose_name_plural = "Employees"

    def __str__(self):
        return f"{self.full_name} ({self.role})"


class Material(models.Model):
    name = models.CharField(max_length=150)
    type = models.CharField(max_length=100, blank=True, null=True)
    color = models.CharField(max_length=80, blank=True, null=True)
    unit = models.CharField(max_length=30, blank=True, null=True)
    stock_qty = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "material"
        ordering = ["name"]
        verbose_name = "Material"
        verbose_name_plural = "Materials"

    def __str__(self):
        return f"{self.name} ({self.color})"


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PRODUCTION = "in_production", "In Production"
        COMPLETED = "completed", "Completed"
        DELIVERED = "delivered", "Delivered"

    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="orders")
    order_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    observations = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "orders"
        ordering = ["-order_date"]
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.pk} - {self.customer.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    garment_type = models.CharField(max_length=100)
    color = models.CharField(max_length=80, blank=True, null=True)
    design_notes = models.TextField(blank=True, null=True)
    quantity = models.IntegerField(default=1)
    materials = models.ManyToManyField(
        Material,
        through="OrderItemMaterial",
        related_name="order_items",
        blank=True,
    )

    class Meta:
        db_table = "order_item"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"{self.garment_type} (Order #{self.order.pk})"


class Measurement(models.Model):
    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="measurement")
    chest = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    waist = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    hips = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    length = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    extra_notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "measurement"
        verbose_name = "Measurement"
        verbose_name_plural = "Measurements"

    def __str__(self):
        return f"Measurements for {self.order_item}"


class WorkTicket(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        DONE = "done", "Done"

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"
        URGENT = "urgent", "Urgent"

    order_item = models.OneToOneField(OrderItem, on_delete=models.CASCADE, related_name="ticket")
    assigned_to = models.ForeignKey(Employee, on_delete=models.SET_NULL, null=True, blank=True, related_name="tickets")
    status = models.CharField(max_length=50, choices=Status.choices, default=Status.PENDING)
    priority = models.CharField(max_length=20, choices=Priority.choices, default=Priority.NORMAL)
    deadline = models.DateField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "work_ticket"
        ordering = ["-priority", "deadline"]
        verbose_name = "Work Ticket"
        verbose_name_plural = "Work Tickets"

    def __str__(self):
        return f"Ticket #{self.pk} - {self.order_item.garment_type} [{self.priority}]"


class ProductionStage(models.Model):
    class StageName(models.TextChoices):
        ORDER_RECEIVED = "order_received", "Order Received"
        DESIGN_CONFIRMED = "design_confirmed", "Design Confirmed"
        CUTTING = "cutting", "Cutting"
        SEWING = "sewing", "Sewing"
        FINISHING = "finishing", "Finishing"
        QUALITY_CHECK = "quality_check", "Quality Check"
        READY_FOR_DELIVERY = "ready_for_delivery", "Ready for Delivery"
        DELIVERED = "delivered", "Delivered"

    work_ticket = models.ForeignKey(WorkTicket, on_delete=models.CASCADE, related_name="stages")
    stage_name = models.CharField(max_length=100, choices=StageName.choices)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    comments = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "production_stage"
        ordering = ["started_at"]
        verbose_name = "Production Stage"
        verbose_name_plural = "Production Stages"

    def __str__(self):
        return f"{self.get_stage_name_display()} - Ticket #{self.work_ticket.pk}"


class Delivery(models.Model):
    class Method(models.TextChoices):
        PICKUP = "pickup", "Pickup"
        COURIER = "courier", "Courier"
        IN_STORE = "in_store", "In Store"

    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="delivery")
    delivery_date = models.DateField(blank=True, null=True)
    method = models.CharField(max_length=80, choices=Method.choices, blank=True, null=True)
    delivered = models.BooleanField(default=False)
    final_comments = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "delivery"
        ordering = ["-delivery_date"]
        verbose_name = "Delivery"
        verbose_name_plural = "Deliveries"

    def __str__(self):
        delivered_status = "Delivered" if self.delivered else "Pending"
        return f"Delivery for Order #{self.order.pk} - {delivered_status}"


class OrderItemMaterial(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE)
    material = models.ForeignKey(Material, on_delete=models.RESTRICT)
    quantity_used = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = "order_item_material"
        unique_together = ("order_item", "material")
        verbose_name = "Order Item Material"
        verbose_name_plural = "Order Item Materials"

    def __str__(self):
        return f"{self.material.name} for {self.order_item}"
