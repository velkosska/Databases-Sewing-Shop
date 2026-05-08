"""Append-only production timeline entries for orders (admin + signals)."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from django.utils.translation import gettext_lazy as _


_depth = 0


@contextmanager
def pause_order_production_logs():
    global _depth
    _depth += 1
    try:
        yield
    finally:
        _depth -= 1


def append_order_production_log(order, kind: str, payload: dict[str, Any] | None = None) -> None:
    if _depth > 0:
        return
    oid = getattr(order, "pk", None)
    if not oid:
        return
    from .models import OrderProductionLog

    OrderProductionLog.objects.create(order_id=int(oid), kind=kind, payload=payload or {})


def _choice_label(choices_dict: dict, code: str | None, plain_fallback: dict[str, str]) -> str:
    if code is None or code == "":
        return "—"
    raw = choices_dict.get(code)
    if raw is not None:
        return str(raw)
    raw = plain_fallback.get(code)
    if raw is not None:
        return str(raw)
    return str(code)


def format_order_production_log_summary(entry: Any) -> str:
    from django.utils.translation import gettext as __

    from .models import Delivery, Order, OrderProductionLog, ProductionStage, WorkTicket

    p = entry.payload or {}
    kind = entry.kind

    order_status = dict(Order.Status.choices)
    pay_status = dict(Order.PaymentStatus.choices)
    ticket_status = dict(WorkTicket.Status.choices)
    stage_choices = dict(ProductionStage.StageName.choices)

    item_plain = {
        "pending": _("Pending"),
        "in_production": _("In Production"),
        "completed": _("Completed"),
    }

    if kind == OrderProductionLog.Kind.ORDER_STATUS:
        a = _choice_label(order_status, p.get("from"), {})
        b = _choice_label(order_status, p.get("to"), {})
        return str(__("Order: %(a)s → %(b)s") % {"a": a, "b": b})

    if kind == OrderProductionLog.Kind.PAYMENT_STATUS:
        a = _choice_label(pay_status, p.get("from"), {})
        b = _choice_label(pay_status, p.get("to"), {})
        return str(__("Payment: %(a)s → %(b)s") % {"a": a, "b": b})

    if kind == OrderProductionLog.Kind.ORDER_ITEM_STATUS:
        g = p.get("garment") or str(__("Item #%(id)s") % {"id": p.get("item_id", "")})
        a = _choice_label({}, p.get("from"), item_plain)
        b = _choice_label({}, p.get("to"), item_plain)
        return str(__('Line "%(g)s": %(a)s → %(b)s') % {"g": g, "a": a, "b": b})

    if kind == OrderProductionLog.Kind.ORDER_ITEM_ASSIGNED:
        g = p.get("garment") or str(__("Item #%(id)s") % {"id": p.get("item_id", "")})
        ae = p.get("from_employee") or "—"
        be = p.get("to_employee") or "—"
        return str(__('Line "%(g)s": %(a)s → %(b)s') % {"g": g, "a": ae, "b": be})

    if kind == OrderProductionLog.Kind.TICKET_STATUS:
        g = p.get("garment") or "—"
        a = _choice_label(ticket_status, p.get("from"), {})
        b = _choice_label(ticket_status, p.get("to"), {})
        return str(__("Ticket #%(tid)s (%(g)s): %(a)s → %(b)s") % {"tid": p.get("ticket_id"), "g": g, "a": a, "b": b})

    if kind == OrderProductionLog.Kind.TICKET_ASSIGNED:
        g = p.get("garment") or "—"
        ae = p.get("from_employee") or str(__("Unassigned"))
        be = p.get("to_employee") or str(__("Unassigned"))
        return str(__("Ticket #%(tid)s (%(g)s) assignee: %(a)s → %(b)s") % {"tid": p.get("ticket_id"), "g": g, "a": ae, "b": be})

    if kind == OrderProductionLog.Kind.STAGE_STARTED:
        stag = str(stage_choices.get(p.get("stage_name"), p.get("stage_name", "—")))
        when = p.get("at") or ""
        if when:
            return str(__("%(stage)s — started (%(when)s)") % {"stage": stag, "when": when})
        return str(__("%(stage)s — started") % {"stage": stag})

    if kind == OrderProductionLog.Kind.STAGE_COMPLETED:
        stag = str(stage_choices.get(p.get("stage_name"), p.get("stage_name", "—")))
        when = p.get("at") or ""
        if when:
            return str(__("%(stage)s — finished (%(when)s)") % {"stage": stag, "when": when})
        return str(__("%(stage)s — finished") % {"stage": stag})

    if kind == OrderProductionLog.Kind.DELIVERY:
        delivered = p.get("delivered")
        method = p.get("method")
        method_l = str(dict(Delivery.Method.choices).get(method, method or "—"))
        at = p.get("delivered_at") or ""
        if delivered:
            return str(__("Delivery: confirmed (%(method)s) %(at)s") % {"method": method_l, "at": at}).strip()
        return str(__("Delivery: pending (%(method)s)") % {"method": method_l})

    return str(p.get("note") or kind)
