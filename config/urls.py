from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import include, path
from django.utils import translation

from shop.api_views import (
    api_catalogue,
    api_create_order,
    api_customer_detail,
    api_customer_measurements,
    api_customers,
    api_dashboard,
    api_deliveries,
    api_employees,
    api_materials,
    api_orders,
    api_production_board,
    api_ticket_status,
)

api_patterns = [
    path("dashboard", api_dashboard, name="api_dashboard"),
    path("orders", api_orders, name="api_orders"),
    path("orders/create", api_create_order, name="api_create_order"),
    path("catalogue", api_catalogue, name="api_catalogue"),
    path("customers", api_customers, name="api_customers"),
    path("customers/<int:customer_id>", api_customer_detail, name="api_customer_detail"),
    path("customers/<int:customer_id>/measurements", api_customer_measurements, name="api_customer_measurements"),
    path("employees", api_employees, name="api_employees"),
    path("materials", api_materials, name="api_materials"),
    path("deliveries", api_deliveries, name="api_deliveries_no_slash"),
    path("deliveries/", api_deliveries, name="api_deliveries"),
    # Next.js api normPath strips trailing slashes; accept both shapes
    path("production/board", api_production_board, name="api_production_board_no_slash"),
    path("production/board/", api_production_board, name="api_production_board"),
    path("tickets/<int:ticket_id>/status", api_ticket_status, name="api_ticket_status_no_slash"),
    path("tickets/<int:ticket_id>/status/", api_ticket_status, name="api_ticket_status"),
]

def set_lang(request, lang_code):
    """GET-friendly language switcher — sets cookie and redirects back."""
    next_url = request.GET.get("next", "/admin/")
    response = HttpResponseRedirect(next_url)
    translation.activate(lang_code)
    response.set_cookie(
        settings.LANGUAGE_COOKIE_NAME,
        lang_code,
        max_age=365 * 24 * 60 * 60,
        path="/",
    )
    return response


urlpatterns = [
    path("i18n/<str:lang_code>/", set_lang, name="set_lang"),
    path("api/", include(api_patterns)),
    path("", include("shop.urls")),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
