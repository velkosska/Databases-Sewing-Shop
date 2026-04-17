from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .models import (
    Customer,
    Delivery,
    Employee,
    Material,
    Measurement,
    Order,
    OrderItem,
    OrderItemMaterial,
    ProductionStage,
    WorkTicket,
)


class MeasurementInline(StackedInline):
    model = Measurement
    extra = 0
    can_delete = False


class OrderItemMaterialInline(TabularInline):
    model = OrderItemMaterial
    extra = 1
    autocomplete_fields = ["material"]


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 1
    fields = ["garment_type", "color", "quantity", "design_notes"]
    show_change_link = True


class ProductionStageInline(TabularInline):
    model = ProductionStage
    extra = 1
    fields = ["stage_name", "started_at", "completed_at", "comments"]


class DeliveryInline(StackedInline):
    model = Delivery
    extra = 0
    can_delete = False


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ["full_name", "phone", "email", "created_at"]
    search_fields = ["full_name", "phone", "email"]
    list_filter = ["created_at"]


@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = ["full_name", "role", "phone", "active"]
    search_fields = ["full_name", "role"]
    list_filter = ["active", "role"]


@admin.register(Material)
class MaterialAdmin(ModelAdmin):
    list_display = ["name", "type", "color", "unit", "stock_qty"]
    search_fields = ["name", "type", "color"]
    list_filter = ["type"]


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ["id", "customer", "order_date", "due_date", "status"]
    search_fields = ["customer__full_name"]
    list_filter = ["status", "order_date", "due_date"]
    ordering = ["-order_date"]
    inlines = [OrderItemInline, DeliveryInline]
    fieldsets = (
        ("Order Info", {"fields": ("customer", "due_date", "status")}),
        ("Notes", {"fields": ("observations",)}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ["id", "order", "garment_type", "color", "quantity"]
    search_fields = ["garment_type", "order__customer__full_name"]
    list_filter = ["garment_type", "color"]
    inlines = [MeasurementInline, OrderItemMaterialInline]


@admin.register(Measurement)
class MeasurementAdmin(ModelAdmin):
    list_display = ["order_item", "chest", "waist", "hips", "length"]
    search_fields = ["order_item__garment_type", "order_item__order__customer__full_name"]


@admin.register(WorkTicket)
class WorkTicketAdmin(ModelAdmin):
    list_display = ["id", "order_item", "assigned_to", "status", "priority", "deadline"]
    search_fields = ["order_item__garment_type", "assigned_to__full_name"]
    list_filter = ["status", "priority", "deadline"]
    inlines = [ProductionStageInline]


@admin.register(ProductionStage)
class ProductionStageAdmin(ModelAdmin):
    list_display = ["work_ticket", "stage_name", "started_at", "completed_at"]
    search_fields = ["work_ticket__id", "stage_name"]
    list_filter = ["stage_name"]


@admin.register(Delivery)
class DeliveryAdmin(ModelAdmin):
    list_display = ["order", "delivery_date", "method", "delivered"]
    search_fields = ["order__customer__full_name"]
    list_filter = ["delivered", "method", "delivery_date"]
