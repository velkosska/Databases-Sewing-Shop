from django.urls import path

from .views import (
    catalogue_item_autofill,
    create_order,
    customer_detail,
    customer_measurements,
    customer_search,
    customer_snapshot,
    dashboard,
    production_board,
    update_ticket_status,
)

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("orders/new/", create_order, name="create_order"),
    path("shop/orders/new/", create_order, name="create_order_shop"),
    path("production/", production_board, name="production_board"),
    path("customers/<int:customer_id>/", customer_detail, name="customer_detail"),

    # JSON APIs
    path("shop/api/catalogue/<int:item_id>/", catalogue_item_autofill, name="catalogue_item_autofill"),
    path("shop/api/customer/<int:customer_id>/measurements/", customer_measurements, name="customer_measurements"),
    path("shop/api/customers/search/", customer_search, name="customer_search"),
    path("shop/api/customer/<int:customer_id>/snapshot/", customer_snapshot, name="customer_snapshot"),
    path("shop/api/ticket/<int:ticket_id>/status/", update_ticket_status, name="update_ticket_status"),
]
