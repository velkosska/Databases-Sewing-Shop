from django.db.models import Count
from django.shortcuts import render
from django.utils import timezone

from .models import Order, WorkTicket


def dashboard(request):
    today = timezone.localdate()
    order_counts = Order.objects.values("status").annotate(total=Count("id"))
    ticket_counts = WorkTicket.objects.values("status").annotate(total=Count("id"))

    context = {
        "pending_orders": Order.objects.filter(status=Order.Status.PENDING).count(),
        "in_production_orders": Order.objects.filter(status=Order.Status.IN_PRODUCTION).count(),
        "overdue_orders": Order.objects.filter(due_date__lt=today).exclude(
            status__in=[Order.Status.COMPLETED, Order.Status.DELIVERED]
        ).count(),
        "completed_orders": Order.objects.filter(status=Order.Status.COMPLETED).count(),
        "delivered_orders": Order.objects.filter(status=Order.Status.DELIVERED).count(),
        "order_status_summary": list(order_counts),
        "ticket_status_summary": list(ticket_counts),
        "recent_orders": Order.objects.select_related("customer").order_by("-order_date")[:10],
    }
    return render(request, "shop/dashboard.html", context)
