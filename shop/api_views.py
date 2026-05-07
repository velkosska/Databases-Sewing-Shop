"""
Thin JSON API consumed by the Next.js frontend.
All endpoints are read-only (GET) except order creation and ticket status updates.
"""
import json
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import ExtractMonth
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (
    Catalogue,
    CatalogueItem,
    Customer,
    Delivery,
    Employee,
    Material,
    Order,
    OrderItem,
    OrderItemMeasurement,
    WorkTicket,
)


def _decimal(v):
    return float(v) if v is not None else None


# ── Dashboard ─────────────────────────────────────────────────────────────

def _pct(current, previous):
    """Return rounded percentage change, or None if previous is zero."""
    if not previous:
        return None
    return round((current - previous) / previous * 100, 1)


def api_dashboard(request):
    today = timezone.localdate()
    orders = (
        Order.objects.select_related("customer")
        .prefetch_related("items__ticket__assigned_to", "items__catalogue_item")
        .order_by("-order_date")
    )

    revenue = Order.objects.aggregate(
        total=Sum("total_price"),
        deposit=Sum("deposit_paid"),
    )
    total_rev = _decimal(revenue["total"]) or 0.0
    total_dep = _decimal(revenue["deposit"]) or 0.0

    balance_outstanding = 0.0
    for o in Order.objects.exclude(status=Order.Status.DELIVERED).only("total_price", "deposit_paid"):
        tp = _decimal(o.total_price) or 0.0
        dp = _decimal(o.deposit_paid) or 0.0
        balance_outstanding += max(tp - dp, 0)

    # ── Period-over-period KPI changes ─────────────────────────────────────
    this_month_start = today.replace(day=1)
    last_month_end   = this_month_start - timedelta(days=1)
    last_month_start = last_month_end.replace(day=1)

    orders_this_month = Order.objects.filter(order_date__gte=this_month_start).count()
    orders_last_month = Order.objects.filter(
        order_date__gte=last_month_start, order_date__lte=last_month_end
    ).count()

    rev_this = Order.objects.filter(order_date__gte=this_month_start).aggregate(
        t=Sum("total_price"))["t"] or 0
    rev_last = Order.objects.filter(
        order_date__gte=last_month_start, order_date__lte=last_month_end
    ).aggregate(t=Sum("total_price"))["t"] or 0

    this_week_start = today - timedelta(days=6)
    last_week_start = this_week_start - timedelta(days=7)
    last_week_end   = this_week_start - timedelta(days=1)

    pending_this = Order.objects.filter(
        status=Order.Status.PENDING, order_date__gte=this_week_start
    ).count()
    pending_last = Order.objects.filter(
        status=Order.Status.PENDING,
        order_date__gte=last_week_start, order_date__lte=last_week_end
    ).count()

    bal_last_month = 0.0
    for o in Order.objects.exclude(status=Order.Status.DELIVERED).filter(
        order_date__gte=last_month_start, order_date__lte=last_month_end
    ).only("total_price", "deposit_paid"):
        bal_last_month += max((_decimal(o.total_price) or 0) - (_decimal(o.deposit_paid) or 0), 0)

    low_stock = []
    for m in Material.objects.filter(low_stock_threshold__isnull=False, stock_quantity__isnull=False):
        if m.is_low_stock:
            low_stock.append({
                "id": m.id,
                "name": m.name,
                "color": m.color,
                "stock_quantity": _decimal(m.stock_quantity),
                "low_stock_threshold": _decimal(m.low_stock_threshold),
            })

    rows = []
    for order in orders:
        first_item = order.items.first()
        ticket = getattr(first_item, "ticket", None) if first_item else None
        assigned_to = ticket.assigned_to.full_name if ticket and ticket.assigned_to else "Unassigned"
        priority = ticket.priority if ticket else "normal"
        garment = first_item.garment_type if first_item and first_item.garment_type else ""
        colour = first_item.color if first_item and first_item.color else ""

        rows.append({
            "id": order.id,
            "customer_id": order.customer_id,
            "customer_name": order.customer.full_name,
            "customer_initials": (order.customer.first_name[:1] + order.customer.last_name[:1]).upper(),
            "garment": garment,
            "color": colour,
            "order_date": order.order_date.isoformat() if order.order_date else None,
            "due_date": order.due_date.isoformat() if order.due_date else None,
            "assigned_to": assigned_to,
            "priority": priority,
            "status": order.status,
            "payment_status": order.payment_status,
            "total_price": _decimal(order.total_price),
        })

    # ── Monthly orders for current year (ExtractMonth works on all backends) ─
    current_year = today.year
    monthly_qs = (
        Order.objects
        .filter(order_date__year=current_year)
        .values(month=ExtractMonth("order_date"))
        .annotate(count=Count("id"))
        .order_by("month")
    )
    MONTH_ABBR = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    monthly_map = {row["month"]: row["count"] for row in monthly_qs}
    monthly_orders = [
        {"month": MONTH_ABBR[m - 1], "orders": monthly_map.get(m, 0)}
        for m in range(1, 13)
    ]

    # ── Daily revenue for the past 7 days ─────────────────────────────────
    # order_date is a DateField so we group directly on the field value
    week_start = today - timedelta(days=6)
    daily_qs = (
        Order.objects
        .filter(order_date__gte=week_start, order_date__lte=today)
        .values("order_date")
        .annotate(revenue=Sum("total_price"))
        .order_by("order_date")
    )
    DAY_ABBR = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
    daily_map = {row["order_date"]: float(row["revenue"] or 0) for row in daily_qs}
    weekly_revenue = [
        {
            "day": DAY_ABBR[(week_start + timedelta(days=i)).weekday()],
            "revenue": round(daily_map.get(week_start + timedelta(days=i), 0), 2),
        }
        for i in range(7)
    ]

    return JsonResponse({
        "stats": {
            "all": Order.objects.count(),
            "pending": Order.objects.filter(status=Order.Status.PENDING).count(),
            "in_production": Order.objects.filter(status=Order.Status.IN_PRODUCTION).count(),
            "overdue": Order.objects.filter(due_date__lt=today).exclude(
                status__in=[Order.Status.COMPLETED, Order.Status.DELIVERED]
            ).count(),
            "completed": Order.objects.filter(status=Order.Status.COMPLETED).count(),
            "delivered": Order.objects.filter(status=Order.Status.DELIVERED).count(),
        },
        "revenue": {
            "total": total_rev,
            "deposit": total_dep,
            "balance_outstanding": round(balance_outstanding, 2),
        },
        "kpi_changes": {
            "orders":  _pct(orders_this_month, orders_last_month),
            "revenue": _pct(float(rev_this), float(rev_last)),
            "pending": _pct(pending_this, pending_last),
            "balance": _pct(balance_outstanding, bal_last_month),
        },
        "charts": {
            "monthly_orders": monthly_orders,
            "weekly_revenue": weekly_revenue,
        },
        "low_stock": low_stock,
        "orders": rows,
        "last_updated": timezone.localtime().strftime("%Y-%m-%d %H:%M"),
    })


# ── Orders ────────────────────────────────────────────────────────────────

def api_orders(request):
    if request.method == "GET":
        orders = Order.objects.select_related("customer").order_by("-order_date")
        data = []
        for o in orders:
            data.append({
                "id": o.id,
                "customer_id": o.customer_id,
                "customer_name": o.customer.full_name,
                "order_date": o.order_date.isoformat() if o.order_date else None,
                "due_date": o.due_date.isoformat() if o.due_date else None,
                "status": o.status,
                "payment_status": o.payment_status,
                "total_price": _decimal(o.total_price),
                "deposit_paid": _decimal(o.deposit_paid),
                "notes": o.notes,
            })
        return JsonResponse({"orders": data})
    return JsonResponse({"error": "Method not allowed"}, status=405)


# ── Order Create ──────────────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST"])
def api_create_order(request):
    try:
        body = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    # Customer
    customer_id = body.get("customer_id")
    new_customer = body.get("new_customer")
    if new_customer:
        first_name = new_customer.get("first_name", "").strip()
        last_name = new_customer.get("last_name", "").strip()
        if not first_name or not last_name:
            return JsonResponse({"error": "First and last name required"}, status=400)
        customer = Customer.objects.create(
            first_name=first_name,
            last_name=last_name,
            phone=new_customer.get("phone") or None,
            email=new_customer.get("email") or None,
            address=new_customer.get("address") or None,
            notes=new_customer.get("notes") or None,
        )
    else:
        customer = Customer.objects.filter(pk=customer_id).first()
        if not customer:
            return JsonResponse({"error": "Customer not found"}, status=400)

    items_payload = body.get("items", [])
    if not items_payload:
        return JsonResponse({"error": "At least one item is required"}, status=400)

    due_date = body.get("due_date") or None
    priority = body.get("priority") or WorkTicket.Priority.NORMAL
    delivery_method = body.get("delivery_method") or "pickup"
    delivery_address = body.get("delivery_address", "").strip()
    delivery_date = body.get("delivery_date") or None
    deposit_method = body.get("deposit_method", "")
    deposit_amount = Decimal(str(body.get("deposit_amount") or "0"))
    order_notes = body.get("order_notes", "").strip()
    internal_notes = body.get("internal_notes", "").strip()
    measurements_payload = body.get("measurements", {})

    with transaction.atomic():
        summary_lines = [
            f"Deposit method: {deposit_method or 'N/A'}",
            f"Deposit paid: {deposit_amount:.2f}",
        ]
        merged_notes = "\n".join(filter(None, [order_notes, internal_notes, *summary_lines]))

        payment_status = Order.PaymentStatus.DEPOSIT if deposit_amount > 0 else Order.PaymentStatus.UNPAID

        order = Order.objects.create(
            customer=customer,
            due_date=due_date,
            status=Order.Status.PENDING,
            deposit_paid=deposit_amount,
            payment_status=payment_status,
            notes=merged_notes or None,
        )

        subtotal = Decimal("0.00")
        for item_data in items_payload:
            source = item_data.get("catalogue_source", "catalogue_item")
            catalogue_item_obj = None
            legacy_catalogue = None
            if source == "catalogue_legacy":
                legacy_catalogue = Catalogue.objects.filter(pk=item_data.get("catalogue_item_id")).first()
                if not legacy_catalogue:
                    continue
                catalogue_name = legacy_catalogue.service
                requires_measurements = True
            else:
                catalogue_item_obj = CatalogueItem.objects.filter(pk=item_data.get("catalogue_item_id")).first()
                if not catalogue_item_obj:
                    continue
                catalogue_name = catalogue_item_obj.name
                requires_measurements = catalogue_item_obj.requires_measurements

            quantity = max(int(item_data.get("quantity", 1)), 1)
            unit_price = Decimal(str(item_data.get("unit_price", "0")))
            line_total = unit_price * quantity

            order_item = OrderItem.objects.create(
                order=order,
                catalogue_item=catalogue_item_obj,
                catalogue=legacy_catalogue,
                garment_type=item_data.get("garment_type") or catalogue_name,
                color_fabric=item_data.get("color_fabric") or "",
                unit_price=unit_price,
                quantity=quantity,
                item_notes=item_data.get("item_notes") or "",
                assigned_employee_id=item_data.get("assigned_employee_id") or None,
                status="pending",
                price_overridden=bool(item_data.get("price_overridden")),
                final_price=line_total,
                color=item_data.get("color_fabric") or None,
                design_notes=item_data.get("item_notes") or None,
            )

            item_meas = item_data.get("measurements", measurements_payload)
            if requires_measurements and any(v for v in item_meas.values() if v):
                OrderItemMeasurement.objects.create(
                    customer=customer,
                    order_item=order_item,
                    bust=item_meas.get("bust") or None,
                    waist=item_meas.get("waist") or None,
                    hips=item_meas.get("hips") or None,
                    shoulder=item_meas.get("shoulder") or None,
                    sleeve=item_meas.get("sleeve") or None,
                    length=item_meas.get("length") or None,
                    inseam=item_meas.get("inseam") or None,
                    neck=item_meas.get("neck") or None,
                    notes=item_meas.get("notes") or None,
                )

            WorkTicket.objects.create(
                order_item=order_item,
                assigned_to_id=item_data.get("assigned_employee_id") or None,
                status=WorkTicket.Status.PENDING,
                priority=priority,
                deadline=due_date,
            )
            subtotal += line_total

        order.total_price = subtotal
        order.save(update_fields=["total_price"])

        if delivery_method == "home_delivery":
            Delivery.objects.create(
                order=order,
                delivery_method=Delivery.Method.COURIER,
                recipient_name=customer.full_name,
                comments=f"Address: {delivery_address}\nRequested: {delivery_date}",
            )

    return JsonResponse({
        "ok": True,
        "order_id": order.id,
        "total_price": float(order.total_price),
        "customer_name": customer.full_name,
        "admin_url": f"/admin/shop/order/{order.id}/change/",
    }, status=201)


# ── Customers ─────────────────────────────────────────────────────────────

def api_customers(request):
    q = request.GET.get("q", "").strip()
    qs = Customer.objects.all()
    if q:
        qs = qs.filter(
            Q(first_name__icontains=q) | Q(last_name__icontains=q)
            | Q(phone__icontains=q) | Q(email__icontains=q)
        )
    data = []
    for c in qs.order_by("first_name", "last_name")[:30]:
        data.append({
            "id": c.id,
            "name": c.full_name,
            "phone": c.phone or "",
            "email": c.email or "",
            "address": c.address or "",
            "order_count": c.orders.count(),
        })
    return JsonResponse({"customers": data})


def api_customer_detail(request, customer_id):
    customer = Customer.objects.filter(pk=customer_id).first()
    if not customer:
        return JsonResponse({"error": "Not found"}, status=404)

    orders = []
    total_spent = 0.0
    for o in customer.orders.prefetch_related("items__catalogue_item").order_by("-order_date"):
        total_spent += float(o.total_price or 0)
        items = []
        for it in o.items.all():
            items.append({
                "id": it.id,
                "garment_type": it.garment_type,
                "catalogue_name": it.catalogue_item.name if it.catalogue_item else None,
                "quantity": it.quantity,
                "final_price": _decimal(it.final_price),
                "color": it.color,
            })
        orders.append({
            "id": o.id,
            "order_date": o.order_date.isoformat() if o.order_date else None,
            "due_date": o.due_date.isoformat() if o.due_date else None,
            "status": o.status,
            "payment_status": o.payment_status,
            "total_price": _decimal(o.total_price),
            "items": items,
        })

    latest_meas = (
        OrderItemMeasurement.objects.filter(customer=customer)
        .order_by("-created_at").first()
    )
    measurements = None
    if latest_meas:
        measurements = {
            "bust": _decimal(latest_meas.bust),
            "waist": _decimal(latest_meas.waist),
            "hips": _decimal(latest_meas.hips),
            "shoulder": _decimal(latest_meas.shoulder),
            "sleeve": _decimal(latest_meas.sleeve),
            "length": _decimal(latest_meas.length),
            "inseam": _decimal(latest_meas.inseam),
            "neck": _decimal(latest_meas.neck),
            "notes": latest_meas.notes,
            "recorded_at": latest_meas.created_at.isoformat(),
        }

    return JsonResponse({
        "id": customer.id,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "full_name": customer.full_name,
        "phone": customer.phone or "",
        "email": customer.email or "",
        "address": customer.address or "",
        "notes": customer.notes or "",
        "created_at": customer.created_at.isoformat() if customer.created_at else None,
        "orders": orders,
        "total_spent": round(total_spent, 2),
        "measurements": measurements,
    })


def api_customer_measurements(request, customer_id):
    meas = (
        OrderItemMeasurement.objects.filter(customer_id=customer_id)
        .select_related("order_item__order")
        .order_by("-created_at")
        .first()
    )
    if not meas:
        return JsonResponse({k: None for k in ["bust","waist","hips","shoulder","sleeve","length","inseam","neck","notes","from_order_date"]})
    return JsonResponse({
        "bust": _decimal(meas.bust),
        "waist": _decimal(meas.waist),
        "hips": _decimal(meas.hips),
        "shoulder": _decimal(meas.shoulder),
        "sleeve": _decimal(meas.sleeve),
        "length": _decimal(meas.length),
        "inseam": _decimal(meas.inseam),
        "neck": _decimal(meas.neck),
        "notes": meas.notes,
        "from_order_date": meas.order_item.order.order_date.isoformat(),
    })


# ── Catalogue ─────────────────────────────────────────────────────────────

def api_catalogue(request):
    items = list(CatalogueItem.objects.order_by("name").values(
        "id", "name", "garment_types", "base_price", "price_hint", "requires_measurements"
    ))
    if not items:
        legacy = list(Catalogue.objects.order_by("service").values("id", "service", "base_price"))
        items = [{
            "id": r["id"], "source": "catalogue_legacy",
            "name": r["service"], "garment_types": [r["service"]],
            "base_price": float(r["base_price"]),
            "price_hint": "", "requires_measurements": True,
        } for r in legacy]
    else:
        for it in items:
            it["source"] = "catalogue_item"
            it["base_price"] = float(it["base_price"])
    return JsonResponse({"catalogue": items})


# ── Employees ─────────────────────────────────────────────────────────────

def api_employees(request):
    employees = Employee.objects.order_by("first_name", "last_name")
    return JsonResponse({
        "employees": [
            {"id": e.id, "name": e.full_name, "role": e.role or ""}
            for e in employees
        ]
    })


# ── Materials ─────────────────────────────────────────────────────────────

def api_materials(request):
    materials = Material.objects.order_by("name")
    return JsonResponse({
        "materials": [
            {
                "id": m.id,
                "name": m.name,
                "color": m.color or "",
                "unit_price": float(m.unit_price),
                "stock_quantity": _decimal(m.stock_quantity),
                "is_low_stock": m.is_low_stock,
            }
            for m in materials
        ]
    })


# ── Production board ──────────────────────────────────────────────────────

def api_production_board(request):
    tickets = (
        WorkTicket.objects.select_related(
            "order_item__order__customer",
            "order_item__catalogue_item",
            "assigned_to",
        )
        .prefetch_related("stages")
        .order_by("-priority", "deadline")
    )

    today = timezone.localdate()
    board = {"pending": [], "in_progress": [], "done": []}

    for ticket in tickets:
        item = ticket.order_item
        customer = item.order.customer
        stages = list(ticket.stages.all())
        current_stage = stages[-1].get_stage_name_display() if stages else "Order Received"
        is_overdue = (
            ticket.deadline
            and (ticket.deadline - today).days < 0
            and ticket.status != WorkTicket.Status.DONE
        )
        board[ticket.status].append({
            "id": ticket.pk,
            "order_id": item.order_id,
            "customer": customer.full_name,
            "garment": item.garment_type or (item.catalogue_item.name.split("  —")[0] if item.catalogue_item else "Item"),
            "color": item.color or "",
            "assigned_to": ticket.assigned_to.full_name if ticket.assigned_to else None,
            "priority": ticket.priority,
            "deadline": ticket.deadline.isoformat() if ticket.deadline else None,
            "is_overdue": is_overdue,
            "current_stage": current_stage,
            "stage_count": len(stages),
        })

    employees = [
        {"id": e.id, "name": e.full_name, "role": e.role or ""}
        for e in Employee.objects.order_by("first_name", "last_name")
    ]

    return JsonResponse({"board": board, "employees": employees})


# ── Ticket status update ──────────────────────────────────────────────────

@csrf_exempt
@require_http_methods(["POST", "PATCH"])
def api_ticket_status(request, ticket_id):
    ticket = WorkTicket.objects.filter(pk=ticket_id).first()
    if not ticket:
        return JsonResponse({"error": "Not found"}, status=404)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    new_status = data.get("status")
    if new_status and new_status not in dict(WorkTicket.Status.choices):
        return JsonResponse({"error": "Invalid status"}, status=400)
    if new_status:
        ticket.status = new_status
    assigned_to_id = data.get("assigned_to_id")
    if assigned_to_id:
        ticket.assigned_to_id = assigned_to_id
    ticket.save()
    return JsonResponse({"ok": True, "status": ticket.status})
