"""Recalculate Order.deposit_paid and Order.payment_status from OrderPayment rows."""

from decimal import Decimal

from django.db.models import Sum


def sync_order_payment_totals(order_id: int) -> None:
    """When payments exist they are authoritative; cumulative total is synced to deposit_paid."""
    from .models import Order, OrderPayment

    qs = OrderPayment.objects.filter(order_id=order_id)
    if not qs.exists():
        return

    paid_raw = qs.aggregate(s=Sum("amount"))["s"]
    paid = paid_raw.quantize(Decimal("0.01")) if paid_raw is not None else Decimal("0.00")

    order = Order.objects.filter(pk=order_id).first()
    if not order:
        return

    total = order.total_price
    if total is None:
        if paid <= 0:
            new_ps = Order.PaymentStatus.UNPAID
        else:
            new_ps = Order.PaymentStatus.DEPOSIT
    else:
        total_d = Decimal(total).quantize(Decimal("0.01"))
        if total_d <= 0:
            new_ps = Order.PaymentStatus.PAID if paid <= 0 else Order.PaymentStatus.DEPOSIT
        elif paid >= total_d:
            new_ps = Order.PaymentStatus.PAID
        elif paid > 0:
            new_ps = Order.PaymentStatus.DEPOSIT
        else:
            new_ps = Order.PaymentStatus.UNPAID

    if order.deposit_paid != paid or order.payment_status != new_ps:
        order.deposit_paid = paid
        order.payment_status = new_ps
        order.save(update_fields=["deposit_paid", "payment_status"])
