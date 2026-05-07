"""
Unit tests for the JSON API views.

Run with:  python manage.py test shop.tests --verbosity=2
"""
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.utils import timezone

from .models import (
    CatalogueItem, Customer, Delivery, Employee,
    Material, Order, OrderItem, WorkTicket,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _json(response):
    return json.loads(response.content)


class BaseTestCase(TestCase):
    """Shared fixtures used across all test classes."""

    def setUp(self):
        self.client = Client()

        self.customer = Customer.objects.create(
            first_name="Ana", last_name="García",
            phone="+34 600 000 001", email="ana@example.com",
        )
        self.employee = Employee.objects.create(
            first_name="Luis", last_name="Martínez", role="Seamstress",
        )
        self.material = Material.objects.create(
            name="Cotton", color="White", unit_price=Decimal("5.00"),
            stock_quantity=Decimal("10.00"), low_stock_threshold=Decimal("20.00"),
        )
        self.catalogue_item = CatalogueItem.objects.create(
            name="Wedding Dress",
            garment_types=["Dress"],
            base_price=Decimal("350.00"),
            requires_measurements=True,
        )
        self.order = Order.objects.create(
            customer=self.customer,
            status=Order.Status.PENDING,
            total_price=Decimal("350.00"),
            deposit_paid=Decimal("100.00"),
            payment_status=Order.PaymentStatus.DEPOSIT,
        )
        self.order_item = OrderItem.objects.create(
            order=self.order,
            catalogue_item=self.catalogue_item,
            garment_type="Wedding Dress",
            unit_price=Decimal("350.00"),
            final_price=Decimal("350.00"),
            quantity=1,
            status="pending",
        )
        self.ticket = WorkTicket.objects.create(
            order_item=self.order_item,
            assigned_to=self.employee,
            status=WorkTicket.Status.PENDING,
            priority=WorkTicket.Priority.NORMAL,
        )


# ── Dashboard ─────────────────────────────────────────────────────────────────

class DashboardAPITest(BaseTestCase):

    def test_returns_200(self):
        r = self.client.get("/api/dashboard")
        self.assertEqual(r.status_code, 200)

    def test_response_keys(self):
        data = _json(self.client.get("/api/dashboard"))
        for key in ("stats", "revenue", "kpi_changes", "charts", "orders", "low_stock"):
            self.assertIn(key, data, f"Missing key: {key}")

    def test_stats_counts(self):
        data = _json(self.client.get("/api/dashboard"))
        self.assertEqual(data["stats"]["all"], 1)
        self.assertEqual(data["stats"]["pending"], 1)
        self.assertEqual(data["stats"]["in_production"], 0)

    def test_revenue_totals(self):
        data = _json(self.client.get("/api/dashboard"))
        self.assertAlmostEqual(data["revenue"]["total"], 350.0, places=2)
        self.assertAlmostEqual(data["revenue"]["deposit"], 100.0, places=2)
        self.assertAlmostEqual(data["revenue"]["balance_outstanding"], 250.0, places=2)

    def test_kpi_changes_present(self):
        data = _json(self.client.get("/api/dashboard"))
        changes = data["kpi_changes"]
        for key in ("orders", "revenue", "pending", "balance"):
            self.assertIn(key, changes)

    def test_charts_monthly_has_12_months(self):
        data = _json(self.client.get("/api/dashboard"))
        self.assertEqual(len(data["charts"]["monthly_orders"]), 12)

    def test_charts_weekly_has_7_days(self):
        data = _json(self.client.get("/api/dashboard"))
        self.assertEqual(len(data["charts"]["weekly_revenue"]), 7)

    def test_low_stock_flagged(self):
        # Cotton has stock=10 below threshold=20 → should appear
        data = _json(self.client.get("/api/dashboard"))
        names = [m["name"] for m in data["low_stock"]]
        self.assertIn("Cotton", names)

    def test_orders_list_in_response(self):
        data = _json(self.client.get("/api/dashboard"))
        self.assertEqual(len(data["orders"]), 1)
        row = data["orders"][0]
        self.assertEqual(row["customer_name"], "Ana García")
        self.assertEqual(row["status"], "pending")


# ── Orders ────────────────────────────────────────────────────────────────────

class OrdersAPITest(BaseTestCase):

    def test_get_orders_200(self):
        r = self.client.get("/api/orders")
        self.assertEqual(r.status_code, 200)

    def test_orders_list(self):
        data = _json(self.client.get("/api/orders"))
        self.assertIn("orders", data)
        self.assertEqual(len(data["orders"]), 1)

    def test_order_fields(self):
        order = _json(self.client.get("/api/orders"))["orders"][0]
        for field in ("id", "customer_id", "customer_name", "order_date", "status", "total_price"):
            self.assertIn(field, order)

    def test_post_not_allowed(self):
        r = self.client.post("/api/orders", content_type="application/json", data="{}")
        self.assertEqual(r.status_code, 405)


# ── Create Order ──────────────────────────────────────────────────────────────

class CreateOrderAPITest(BaseTestCase):

    def _post(self, payload):
        return self.client.post(
            "/api/orders/create",
            data=json.dumps(payload),
            content_type="application/json",
        )

    def test_create_with_existing_customer(self):
        payload = {
            "customer_id": self.customer.pk,
            "items": [{
                "catalogue_item_id": self.catalogue_item.pk,
                "catalogue_source": "catalogue_item",
                "garment_type": "Wedding Dress",
                "quantity": 1,
                "unit_price": "350.00",
            }],
            "due_date": None,
            "priority": "normal",
            "delivery_method": "pickup",
            "deposit_method": "cash",
            "deposit_amount": "100",
            "measurements": {},
        }
        r = self._post(payload)
        self.assertEqual(r.status_code, 201)
        data = _json(r)
        self.assertTrue(data["ok"])
        self.assertIn("order_id", data)
        self.assertEqual(data["customer_name"], "Ana García")

    def test_create_with_new_customer(self):
        payload = {
            "new_customer": {"first_name": "Maria", "last_name": "López"},
            "items": [{
                "catalogue_item_id": self.catalogue_item.pk,
                "catalogue_source": "catalogue_item",
                "quantity": 1,
                "unit_price": "200.00",
            }],
            "delivery_method": "pickup",
            "deposit_amount": "0",
            "measurements": {},
        }
        r = self._post(payload)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(Customer.objects.filter(first_name="Maria", last_name="López").exists())

    def test_missing_items_returns_400(self):
        r = self._post({"customer_id": self.customer.pk, "items": []})
        self.assertEqual(r.status_code, 400)

    def test_missing_customer_returns_400(self):
        r = self._post({"items": [{"catalogue_item_id": self.catalogue_item.pk, "quantity": 1, "unit_price": "100"}]})
        self.assertEqual(r.status_code, 400)

    def test_new_customer_missing_name_returns_400(self):
        r = self._post({
            "new_customer": {"first_name": "", "last_name": ""},
            "items": [{"catalogue_item_id": self.catalogue_item.pk, "quantity": 1, "unit_price": "100"}],
        })
        self.assertEqual(r.status_code, 400)

    def test_work_tickets_created(self):
        before = WorkTicket.objects.count()
        self._post({
            "customer_id": self.customer.pk,
            "items": [{"catalogue_item_id": self.catalogue_item.pk, "catalogue_source": "catalogue_item", "quantity": 1, "unit_price": "50"}],
            "delivery_method": "pickup", "deposit_amount": "0", "measurements": {},
        })
        self.assertEqual(WorkTicket.objects.count(), before + 1)

    def test_deposit_sets_payment_status(self):
        r = self._post({
            "customer_id": self.customer.pk,
            "items": [{"catalogue_item_id": self.catalogue_item.pk, "catalogue_source": "catalogue_item", "quantity": 1, "unit_price": "200"}],
            "delivery_method": "pickup", "deposit_amount": "50", "measurements": {},
        })
        order_id = _json(r)["order_id"]
        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.payment_status, Order.PaymentStatus.DEPOSIT)

    def test_no_deposit_unpaid_status(self):
        r = self._post({
            "customer_id": self.customer.pk,
            "items": [{"catalogue_item_id": self.catalogue_item.pk, "catalogue_source": "catalogue_item", "quantity": 1, "unit_price": "200"}],
            "delivery_method": "pickup", "deposit_amount": "0", "measurements": {},
        })
        order_id = _json(r)["order_id"]
        order = Order.objects.get(pk=order_id)
        self.assertEqual(order.payment_status, Order.PaymentStatus.UNPAID)

    def test_home_delivery_creates_delivery_record(self):
        r = self._post({
            "customer_id": self.customer.pk,
            "items": [{"catalogue_item_id": self.catalogue_item.pk, "catalogue_source": "catalogue_item", "quantity": 1, "unit_price": "200"}],
            "delivery_method": "home_delivery",
            "delivery_address": "Calle Mayor 1", "delivery_date": "2026-06-01",
            "deposit_amount": "0", "measurements": {},
        })
        order_id = _json(r)["order_id"]
        self.assertTrue(Delivery.objects.filter(order_id=order_id).exists())


# ── Customers ─────────────────────────────────────────────────────────────────

class CustomersAPITest(BaseTestCase):

    def test_list_200(self):
        r = self.client.get("/api/customers")
        self.assertEqual(r.status_code, 200)

    def test_list_contains_customer(self):
        data = _json(self.client.get("/api/customers"))
        names = [c["name"] for c in data["customers"]]
        self.assertIn("Ana García", names)

    def test_search_by_name(self):
        Customer.objects.create(first_name="Pedro", last_name="Vega")
        data = _json(self.client.get("/api/customers?q=Pedro"))
        self.assertEqual(len(data["customers"]), 1)
        self.assertEqual(data["customers"][0]["name"], "Pedro Vega")

    def test_search_no_match(self):
        data = _json(self.client.get("/api/customers?q=ZZZZZZ"))
        self.assertEqual(len(data["customers"]), 0)

    def test_detail_200(self):
        r = self.client.get(f"/api/customers/{self.customer.pk}")
        self.assertEqual(r.status_code, 200)

    def test_detail_fields(self):
        data = _json(self.client.get(f"/api/customers/{self.customer.pk}"))
        self.assertEqual(data["full_name"], "Ana García")
        self.assertIn("orders", data)
        self.assertIn("measurements", data)

    def test_detail_not_found(self):
        r = self.client.get("/api/customers/999999")
        self.assertEqual(r.status_code, 404)

    def test_detail_includes_orders(self):
        data = _json(self.client.get(f"/api/customers/{self.customer.pk}"))
        self.assertEqual(len(data["orders"]), 1)
        self.assertAlmostEqual(data["total_spent"], 350.0, places=2)


# ── Catalogue ─────────────────────────────────────────────────────────────────

class CatalogueAPITest(BaseTestCase):

    def test_list_200(self):
        r = self.client.get("/api/catalogue")
        self.assertEqual(r.status_code, 200)

    def test_contains_item(self):
        data = _json(self.client.get("/api/catalogue"))
        names = [i["name"] for i in data["catalogue"]]
        self.assertIn("Wedding Dress", names)

    def test_item_has_required_fields(self):
        item = _json(self.client.get("/api/catalogue"))["catalogue"][0]
        for field in ("id", "name", "base_price", "requires_measurements", "source"):
            self.assertIn(field, item)


# ── Employees ─────────────────────────────────────────────────────────────────

class EmployeesAPITest(BaseTestCase):

    def test_list_200(self):
        r = self.client.get("/api/employees")
        self.assertEqual(r.status_code, 200)

    def test_contains_employee(self):
        data = _json(self.client.get("/api/employees"))
        names = [e["name"] for e in data["employees"]]
        self.assertIn("Luis Martínez", names)


# ── Materials ─────────────────────────────────────────────────────────────────

class MaterialsAPITest(BaseTestCase):

    def test_list_200(self):
        r = self.client.get("/api/materials")
        self.assertEqual(r.status_code, 200)

    def test_low_stock_flagged(self):
        data = _json(self.client.get("/api/materials"))
        cotton = next(m for m in data["materials"] if m["name"] == "Cotton")
        self.assertTrue(cotton["is_low_stock"])


# ── Production Board ──────────────────────────────────────────────────────────

class ProductionBoardAPITest(BaseTestCase):

    def test_board_200(self):
        r = self.client.get("/api/production/board")
        self.assertEqual(r.status_code, 200)

    def test_board_structure(self):
        data = _json(self.client.get("/api/production/board"))
        self.assertIn("board", data)
        self.assertIn("employees", data)
        for col in ("pending", "in_progress", "done"):
            self.assertIn(col, data["board"])

    def test_ticket_in_pending_column(self):
        data = _json(self.client.get("/api/production/board"))
        self.assertEqual(len(data["board"]["pending"]), 1)
        self.assertEqual(data["board"]["pending"][0]["customer"], "Ana García")


# ── Ticket Status Update ──────────────────────────────────────────────────────

class TicketStatusAPITest(BaseTestCase):

    def test_update_status(self):
        r = self.client.post(
            f"/api/tickets/{self.ticket.pk}/status",
            data=json.dumps({"status": "in_progress"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 200)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.status, "in_progress")

    def test_invalid_status_400(self):
        r = self.client.post(
            f"/api/tickets/{self.ticket.pk}/status",
            data=json.dumps({"status": "flying"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 400)

    def test_not_found_404(self):
        r = self.client.post(
            "/api/tickets/999999/status",
            data=json.dumps({"status": "done"}),
            content_type="application/json",
        )
        self.assertEqual(r.status_code, 404)


# ── Language Switcher ─────────────────────────────────────────────────────────

class LanguageSwitcherTest(TestCase):

    def setUp(self):
        self.client = Client()

    def test_set_english(self):
        r = self.client.get("/i18n/en/?next=/admin/")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r["Location"], "/admin/")
        self.assertIn("django_language", r.cookies)
        self.assertEqual(r.cookies["django_language"].value, "en")

    def test_set_spanish(self):
        r = self.client.get("/i18n/es/?next=/admin/")
        self.assertEqual(r.status_code, 302)
        self.assertEqual(r.cookies["django_language"].value, "es")
