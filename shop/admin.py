from django.contrib import admin
from unfold.admin import ModelAdmin, StackedInline, TabularInline

from .models import (
    Catalogue,
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


class OrderItemMaterialInline(TabularInline):
    model = OrderItemMaterial
    extra = 1
    autocomplete_fields = ["material"]


class OrderItemInline(TabularInline):
    model = OrderItem
    extra = 1
    fields = ["catalogue", "garment_type", "color", "quantity", "status", "final_price", "design_notes"]
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
    list_display = ["first_name", "last_name", "phone", "email", "created_at"]
    search_fields = ["first_name", "last_name", "phone", "email"]
    list_filter = ["created_at"]


@admin.register(Employee)
class EmployeeAdmin(ModelAdmin):
    list_display = ["first_name", "last_name", "role", "phone"]
    search_fields = ["first_name", "last_name", "role"]
    list_filter = ["role"]


@admin.register(Material)
class MaterialAdmin(ModelAdmin):
    list_display = ["name", "color", "unit_price", "stock_quantity"]
    search_fields = ["name", "color"]


@admin.register(Catalogue)
class CatalogueAdmin(ModelAdmin):
    list_display = ["service", "base_price"]
    search_fields = ["service"]


@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ["id", "customer", "order_date", "due_date", "status", "total_price"]
    search_fields = ["customer__first_name", "customer__last_name"]
    list_filter = ["status", "order_date", "due_date"]
    ordering = ["-order_date"]
    inlines = [OrderItemInline, DeliveryInline]
    fieldsets = (
        ("Order Info", {"fields": ("customer", "due_date", "status")}),
        ("Pricing & Notes", {"fields": ("total_price", "notes")}),
    )


@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ["id", "order", "catalogue", "garment_type", "quantity", "status", "final_price"]
    search_fields = ["garment_type", "catalogue__service", "order__customer__first_name", "order__customer__last_name"]
    list_filter = ["catalogue", "status", "color"]
    inlines = [OrderItemMaterialInline]


@admin.register(Measurement)
class MeasurementAdmin(ModelAdmin):
    list_display = ["customer", "chest", "waist", "hip", "shoulder", "sleeve_length", "inseam", "updated_at"]
    search_fields = ["customer__first_name", "customer__last_name"]


@admin.register(WorkTicket)
class WorkTicketAdmin(ModelAdmin):
    list_display = ["id", "order_item", "assigned_to", "status", "priority", "deadline", "created_at"]
    search_fields = ["order_item__garment_type", "assigned_to__first_name", "assigned_to__last_name"]
    list_filter = ["status", "priority", "deadline"]
    inlines = [ProductionStageInline]


@admin.register(ProductionStage)
class ProductionStageAdmin(ModelAdmin):
    list_display = ["work_ticket", "stage_name", "started_at", "completed_at"]
    search_fields = ["work_ticket__id", "stage_name"]
    list_filter = ["stage_name"]


@admin.register(Delivery)
class DeliveryAdmin(ModelAdmin):
    list_display = ["order", "delivered_at", "delivery_method", "recipient_name", "delivered"]
    search_fields = ["order__customer__first_name", "order__customer__last_name", "recipient_name"]
    list_filter = ["delivered", "delivery_method", "delivered_at"]
