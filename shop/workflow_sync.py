"""Keep Order / OrderItem status aligned with work tickets (workflow 2 → 3)."""

from django.db import transaction

from .models import Order, WorkTicket


def refresh_order_aggregate_status(order):
    """Sync aggregate order status and order line statuses from all work tickets."""
    if order.status == Order.Status.DELIVERED:
        return

    tickets = list(
        WorkTicket.objects.filter(order_item__order_id=order.pk).select_related("order_item")
    )
    if not tickets:
        return

    statuses = [t.status for t in tickets]
    all_done = all(s == WorkTicket.Status.DONE for s in statuses)
    any_in_progress = any(s == WorkTicket.Status.IN_PROGRESS for s in statuses)
    partial_done = any(s == WorkTicket.Status.DONE for s in statuses) and not all_done

    if all_done:
        new_order_status = Order.Status.COMPLETED
    elif any_in_progress or partial_done:
        new_order_status = Order.Status.IN_PRODUCTION
    else:
        new_order_status = Order.Status.PENDING

    ticket_to_item = {
        WorkTicket.Status.PENDING: "pending",
        WorkTicket.Status.IN_PROGRESS: "in_production",
        WorkTicket.Status.DONE: "completed",
    }

    with transaction.atomic():
        order_seen = Order.objects.filter(pk=order.pk).exclude(
            status=Order.Status.DELIVERED,
        ).first()
        if not order_seen:
            return

        for t in tickets:
            want = ticket_to_item.get(t.status)
            if want is None:
                continue
            oi = t.order_item
            if oi.status != want:
                oi.status = want
                oi.save(update_fields=["status"])

        if order_seen.status != new_order_status:
            order_seen.status = new_order_status
            order_seen.save(update_fields=["status"])
