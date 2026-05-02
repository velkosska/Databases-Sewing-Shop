from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from .models import Order, WorkTicket


def dashboard(request):
    today = timezone.localdate()
    order_counts = Order.objects.values("status").annotate(total=Count("id"))
    ticket_counts = WorkTicket.objects.values("status").annotate(total=Count("id"))
    orders = (
        Order.objects.select_related("customer")
        .prefetch_related("items__ticket__assigned_to")
        .order_by("-order_date")
    )

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

        table_rows.append(
            {
                "id": order.id,
                "customer_name": order.customer.full_name,
                "customer_initials": f"{order.customer.first_name[:1]}{order.customer.last_name[:1]}".upper(),
                "garment": garment,
                "color": first_item.color if first_item and first_item.color else "",
                "order_date": order.order_date.isoformat() if order.order_date else "",
                "due_date": order.due_date.isoformat() if order.due_date else "",
                "assigned_to": assigned_to,
                "priority": priority,
                "status": order.status,
                "overdue_days": overdue_days,
                "due_in_days": due_in_days,
            }
        )

    context = {
        "pending_orders": Order.objects.filter(status=Order.Status.PENDING).count(),
        "in_production_orders": Order.objects.filter(status=Order.Status.IN_PRODUCTION).count(),
        "overdue_orders": Order.objects.filter(due_date__lt=today).exclude(
            status__in=[Order.Status.COMPLETED, Order.Status.DELIVERED]
        ).count(),
        "completed_orders": Order.objects.filter(status=Order.Status.COMPLETED).count(),
        "delivered_orders": Order.objects.filter(status=Order.Status.DELIVERED).count(),
        "all_orders": Order.objects.count(),
        "order_status_summary": list(order_counts),
        "ticket_status_summary": list(ticket_counts),
        "recent_orders": Order.objects.select_related("customer").order_by("-order_date")[:10],
        "table_rows": table_rows,
        "last_updated": timezone.localtime().strftime("%Y-%m-%d %H:%M"),
    }
    return render(request, "shop/dashboard.html", context)
