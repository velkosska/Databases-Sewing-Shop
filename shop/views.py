import json
from decimal import Decimal

from django.contrib import messages
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

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


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _catalogue_payload():
    items = list(
        CatalogueItem.objects.order_by("name").values(
            "id", "name", "garment_types", "base_price", "price_hint", "requires_measurements"
        )
    )
    if items:
        return [{"source": "catalogue_item", **item} for item in items]

    legacy = list(Catalogue.objects.order_by("service").values("id", "service", "base_price"))
    return [
        {
            "id": row["id"],
            "source": "catalogue_legacy",
            "name": row["service"],
            "garment_types": [row["service"]],
            "base_price": str(row["base_price"]),
            "price_hint": "Base price from existing catalogue",
            "requires_measurements": True,
        }
        for row in legacy
    ]


# ─── Dashboard ───────────────────────────────────────────────────────────────

def dashboard(request):
    today = timezone.localdate()
    order_counts = Order.objects.values("status").annotate(total=Count("id"))
    ticket_counts = WorkTicket.objects.values("status").annotate(total=Count("id"))
    orders = (
        Order.objects.select_related("customer")
        .prefetch_related("items__ticket__assigned_to", "items__catalogue_item")
        .order_by("-order_date")
    )

    revenue_data = Order.objects.aggregate(
        total_revenue=Sum("total_price"),
        total_deposit=Sum("deposit_paid"),
    )
    total_revenue = revenue_data["total_revenue"] or Decimal("0.00")
    total_deposit = revenue_data["total_deposit"] or Decimal("0.00")
    balance_outstanding = sum(
        o.balance_due for o in Order.objects.exclude(
            status__in=[Order.Status.DELIVERED]
        ).only("total_price", "deposit_paid")
    )

    low_stock_materials = Material.objects.filter(
        low_stock_threshold__isnull=False,
        stock_quantity__isnull=False,
    ).extra(
        where=["stock_quantity <= low_stock_threshold"]
    ).order_by("name")

    table_rows = []
    for order in orders:
        first_item = order.items.first()
        ticket = getattr(first_item, "ticket", None) if first_item else None
        assigned_to = ticket.assigned_to.full_name if ticket and ticket.assigned_to else "Unassigned"
        priority = ticket.priority if ticket else "normal"
        garment = first_item.garment_type if first_item and first_item.garment_type else "N/A"
        due_in_days = None
        overdue_days = None
        if order.due_date:
            day_delta = (order.due_date - today).days
            if day_delta < 0 and order.status not in (Order.Status.COMPLETED, Order.Status.DELIVERED):
                overdue_days = abs(day_delta)
            elif day_delta <= 3 and order.status not in (Order.Status.COMPLETED, Order.Status.DELIVERED):
                due_in_days = day_delta

        table_rows.append({
            "id": order.id,
            "customer_id": order.customer_id,
            "customer_name": order.customer.full_name,
            "customer_initials": f"{order.customer.first_name[:1]}{order.customer.last_name[:1]}".upper(),
            "garment": garment,
            "color": first_item.color if first_item and first_item.color else "",
            "order_date": order.order_date.isoformat() if order.order_date else "",
            "due_date": order.due_date.isoformat() if order.due_date else "",
            "assigned_to": assigned_to,
            "priority": priority,
            "status": order.status,
            "payment_status": order.payment_status,
            "total_price": str(order.total_price) if order.total_price else "0.00",
            "overdue_days": overdue_days,
            "due_in_days": due_in_days,
        })

    context = {
        "pending_orders": Order.objects.filter(status=Order.Status.PENDING).count(),
        "in_production_orders": Order.objects.filter(status=Order.Status.IN_PRODUCTION).count(),
        "overdue_orders": Order.objects.filter(due_date__lt=today).exclude(
            status__in=[Order.Status.COMPLETED, Order.Status.DELIVERED]
        ).count(),
        "completed_orders": Order.objects.filter(status=Order.Status.COMPLETED).count(),
        "delivered_orders": Order.objects.filter(status=Order.Status.DELIVERED).count(),
        "all_orders": Order.objects.count(),
        "total_revenue": total_revenue,
        "total_deposit": total_deposit,
        "balance_outstanding": balance_outstanding,
        "low_stock_materials": low_stock_materials,
        "order_status_summary": list(order_counts),
        "ticket_status_summary": list(ticket_counts),
        "table_rows": table_rows,
        "last_updated": timezone.localtime().strftime("%Y-%m-%d %H:%M"),
    }
    return render(request, "shop/dashboard.html", context)


# ─── Order Wizard ─────────────────────────────────────────────────────────────

def create_order(request):
    catalogue_items = _catalogue_payload()
    employees = Employee.objects.order_by("first_name", "last_name")
    customers = Customer.objects.order_by("first_name", "last_name")
    priorities = [{"value": value, "label": label} for value, label in WorkTicket.Priority.choices]
    materials = list(
        Material.objects.order_by("name").values("id", "name", "color", "unit_price", "stock_quantity")
    )

    if request.method == "POST":
        # ── Customer resolution ─────────────────────────────────────────
        customer_id = request.POST.get("customer_id")
        create_new = request.POST.get("create_new_customer") == "1"

        if create_new:
            first_name = request.POST.get("new_first_name", "").strip()
            last_name = request.POST.get("new_last_name", "").strip()
            phone = request.POST.get("new_phone", "").strip()
            email = request.POST.get("new_email", "").strip()
            address = request.POST.get("new_address", "").strip()
            customer_notes = request.POST.get("new_customer_notes", "").strip()
            if not first_name or not last_name:
                messages.error(request, "First and last name are required for a new customer.")
                return redirect("create_order_shop")
            customer = Customer.objects.create(
                first_name=first_name,
                last_name=last_name,
                phone=phone or None,
                email=email or None,
                address=address or None,
                notes=customer_notes or None,
            )
        else:
            customer = Customer.objects.filter(pk=customer_id).first()

        due_date = request.POST.get("due_date") or None
        priority = request.POST.get("priority") or WorkTicket.Priority.NORMAL
        delivery_method = request.POST.get("delivery_method") or "pickup"
        delivery_address = request.POST.get("delivery_address", "").strip()
        delivery_date = request.POST.get("delivery_date") or None
        deposit_method = request.POST.get("deposit_method", "").strip()
        deposit_amount_str = request.POST.get("deposit_amount") or "0"
        internal_notes = request.POST.get("internal_notes", "").strip()
        order_notes = request.POST.get("order_notes", "").strip()

        try:
            deposit_amount = Decimal(deposit_amount_str)
        except Exception:
            deposit_amount = Decimal("0.00")

        try:
            items_payload = json.loads(request.POST.get("items_json", "[]"))
            measurements_payload = json.loads(request.POST.get("measurements_json", "{}"))
        except json.JSONDecodeError:
            return HttpResponseBadRequest("Invalid payload.")

        if not customer or not items_payload:
            messages.error(request, "Select a customer and add at least one item.")
            return redirect("create_order_shop")

        with transaction.atomic():
            summary_lines = [
                f"Deposit method: {deposit_method or 'N/A'}",
                f"Deposit paid: {deposit_amount:.2f}",
            ]
            merged_notes = "\n".join(filter(None, [order_notes, internal_notes, *summary_lines]))

            payment_status = Order.PaymentStatus.UNPAID
            if deposit_amount > 0:
                payment_status = Order.PaymentStatus.DEPOSIT

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
                    status=item_data.get("status") or "pending",
                    price_overridden=bool(item_data.get("price_overridden")),
                    final_price=line_total,
                    color=item_data.get("color_fabric") or None,
                    design_notes=item_data.get("item_notes") or None,
                )

                item_measurements = item_data.get("measurements", measurements_payload)
                if requires_measurements and any(v for v in item_measurements.values() if v):
                    OrderItemMeasurement.objects.create(
                        customer=customer,
                        order_item=order_item,
                        bust=item_measurements.get("bust") or None,
                        waist=item_measurements.get("waist") or None,
                        hips=item_measurements.get("hips") or None,
                        shoulder=item_measurements.get("shoulder") or None,
                        sleeve=item_measurements.get("sleeve") or None,
                        length=item_measurements.get("length") or None,
                        inseam=item_measurements.get("inseam") or None,
                        neck=item_measurements.get("neck") or None,
                        notes=item_measurements.get("notes") or None,
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
                    comments=f"Address: {delivery_address}\nRequested date: {delivery_date}",
                )

        messages.success(request, f"Order #{order.id} created — {len(items_payload)} item(s), total ${order.total_price:.2f}.")
        return redirect(f"/admin/shop/order/{order.id}/change/")

    context = {
        "catalogue_items": catalogue_items,
        "employees": [{"id": emp.id, "name": emp.full_name, "role": emp.role or ""} for emp in employees],
        "customers": [
            {
                "id": c.id,
                "name": c.full_name,
                "phone": c.phone or "",
                "email": c.email or "",
                "address": c.address or "",
                "order_count": c.orders.count(),
            }
            for c in customers
        ],
        "priorities": priorities,
        "materials": materials,
    }
    return render(request, "shop/order_wizard.html", context)


# ─── Production Board ────────────────────────────────────────────────────────

def production_board(request):
    tickets = (
        WorkTicket.objects.select_related(
            "order_item__order__customer",
            "order_item__catalogue_item",
            "assigned_to",
        )
        .prefetch_related("stages")
        .order_by("-priority", "deadline")
    )

    # Group by status
    board = {
        "pending": [],
        "in_progress": [],
        "done": [],
    }
    today = timezone.localdate()
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
            "garment": item.garment_type or (item.catalogue_item.name if item.catalogue_item else "Item"),
            "color": item.color or "",
            "assigned_to": ticket.assigned_to.full_name if ticket.assigned_to else "Unassigned",
            "priority": ticket.priority,
            "deadline": ticket.deadline.isoformat() if ticket.deadline else "",
            "is_overdue": is_overdue,
            "current_stage": current_stage,
            "stage_count": len(stages),
        })

    employees = Employee.objects.order_by("first_name", "last_name")

    context = {
        "board": board,
        "pending_count": len(board["pending"]),
        "in_progress_count": len(board["in_progress"]),
        "done_count": len(board["done"]),
        "employees": employees,
        "today": today,
    }
    return render(request, "shop/production_board.html", context)


# ─── Customer Detail ─────────────────────────────────────────────────────────

def customer_detail(request, customer_id):
    customer = get_object_or_404(Customer, pk=customer_id)
    orders = (
        customer.orders
        .prefetch_related("items__catalogue_item", "items__ticket")
        .order_by("-order_date")
    )
    latest_measurement = (
        OrderItemMeasurement.objects.filter(customer=customer)
        .order_by("-created_at")
        .first()
    )
    total_spent = orders.aggregate(total=Sum("total_price"))["total"] or Decimal("0.00")

    context = {
        "customer": customer,
        "orders": orders,
        "latest_measurement": latest_measurement,
        "total_spent": total_spent,
        "order_count": orders.count(),
    }
    return render(request, "shop/customer_detail.html", context)


# ─── API: Catalogue autofill ─────────────────────────────────────────────────

def catalogue_item_autofill(request, item_id):
    source = request.GET.get("source", "catalogue_item")
    if source == "catalogue_legacy":
        item = Catalogue.objects.filter(pk=item_id).first()
        if not item:
            return JsonResponse({"detail": "Not found."}, status=404)
        return JsonResponse({
            "name": item.service,
            "garment_types": [item.service],
            "base_price": f"{item.base_price:.2f}",
            "price_hint": "Base price from existing catalogue",
            "requires_measurements": True,
        })

    item = CatalogueItem.objects.filter(pk=item_id).first()
    if not item:
        return JsonResponse({"detail": "Not found."}, status=404)
    return JsonResponse({
        "name": item.name,
        "garment_types": item.garment_types,
        "base_price": f"{item.base_price:.2f}",
        "price_hint": item.price_hint,
        "requires_measurements": item.requires_measurements,
    })


# ─── API: Customer measurements ──────────────────────────────────────────────

def customer_measurements(request, customer_id):
    measurement = (
        OrderItemMeasurement.objects.filter(customer_id=customer_id)
        .select_related("order_item__order")
        .order_by("-created_at")
        .first()
    )
    if not measurement:
        return JsonResponse({
            "bust": None, "waist": None, "hips": None,
            "shoulder": None, "sleeve": None, "length": None,
            "inseam": None, "neck": None, "notes": None,
            "from_order_date": None,
        })
    return JsonResponse({
        "bust": str(measurement.bust) if measurement.bust else None,
        "waist": str(measurement.waist) if measurement.waist else None,
        "hips": str(measurement.hips) if measurement.hips else None,
        "shoulder": str(measurement.shoulder) if measurement.shoulder else None,
        "sleeve": str(measurement.sleeve) if measurement.sleeve else None,
        "length": str(measurement.length) if measurement.length else None,
        "inseam": str(measurement.inseam) if measurement.inseam else None,
        "neck": str(measurement.neck) if measurement.neck else None,
        "notes": measurement.notes,
        "from_order_date": measurement.order_item.order.order_date.isoformat(),
    })


# ─── API: Customer search ─────────────────────────────────────────────────────

def customer_search(request):
    query = request.GET.get("q", "").strip()
    customers = Customer.objects.all()
    if query:
        customers = customers.filter(
            Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(phone__icontains=query)
            | Q(email__icontains=query)
        )
    data = []
    for customer in customers.order_by("first_name", "last_name")[:20]:
        data.append({
            "id": customer.id,
            "name": customer.full_name,
            "phone": customer.phone or "",
            "email": customer.email or "",
            "address": customer.address or "",
            "order_count": customer.orders.count(),
        })
    return JsonResponse({"results": data})


# ─── API: Customer snapshot ───────────────────────────────────────────────────

def customer_snapshot(request, customer_id):
    customer = Customer.objects.filter(pk=customer_id).first()
    if not customer:
        return JsonResponse({"detail": "Not found."}, status=404)
    latest_measurement = (
        OrderItemMeasurement.objects.filter(customer_id=customer_id)
        .order_by("-created_at")
        .first()
    )
    return JsonResponse({
        "id": customer.id,
        "name": customer.full_name,
        "phone": customer.phone or "",
        "email": customer.email or "",
        "address": customer.address or "",
        "notes": customer.notes or "",
        "orders_count": customer.orders.count(),
        "latest_measurement_note": latest_measurement.notes if latest_measurement else "",
    })


# ─── API: Update ticket status ─────────────────────────────────────────────

def update_ticket_status(request, ticket_id):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    ticket = WorkTicket.objects.filter(pk=ticket_id).first()
    if not ticket:
        return JsonResponse({"error": "Not found"}, status=404)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    new_status = data.get("status")
    if new_status not in dict(WorkTicket.Status.choices):
        return JsonResponse({"error": "Invalid status"}, status=400)
    ticket.status = new_status
    assigned_to_id = data.get("assigned_to_id")
    if assigned_to_id:
        ticket.assigned_to_id = assigned_to_id
    ticket.save()
    return JsonResponse({"ok": True, "status": ticket.status})
