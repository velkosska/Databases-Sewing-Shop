"""Wizard / API measurement prefill: latest order-line row, else Customer.measurement profile."""
from __future__ import annotations

from typing import Any

from .models import Measurement, OrderItemMeasurement

_MEAS_KEYS = (
    "bust", "waist", "hips", "shoulder", "sleeve", "length", "inseam", "neck",
)


def _empty_prefill() -> dict[str, Any]:
    return {
        **_empty_measures(),
        "notes": None,
        "from_order_date": None,
        "prefill_source": None,
        "recorded_at": None,
    }


def _empty_measures() -> dict[str, Any]:
    return {k: None for k in _MEAS_KEYS}


def get_customer_wizard_measurement_prefill(customer_id: int) -> dict[str, Any]:
    """
    Values for body fields are Decimals or None.
    from_order_date is an ISO date string when any prefill exists (order date or profile updated date).
    """
    item_meas = (
        OrderItemMeasurement.objects.filter(customer_id=customer_id)
        .select_related("order_item__order")
        .order_by("-created_at")
        .first()
    )
    if item_meas:
        od = item_meas.order_item.order.order_date
        return {
            "bust": item_meas.bust,
            "waist": item_meas.waist,
            "hips": item_meas.hips,
            "shoulder": item_meas.shoulder,
            "sleeve": item_meas.sleeve,
            "length": item_meas.length,
            "inseam": item_meas.inseam,
            "neck": item_meas.neck,
            "notes": item_meas.notes,
            "from_order_date": od.isoformat() if od else None,
            "prefill_source": "order",
            "recorded_at": item_meas.created_at,
        }

    prof = Measurement.objects.filter(customer_id=customer_id).first()
    if not prof:
        return _empty_prefill()

    has_values = any(
        v is not None
        for v in (
            prof.chest,
            prof.waist,
            prof.hip,
            prof.shoulder,
            prof.sleeve_length,
            prof.inseam,
            prof.notes,
        )
    )
    if not has_values:
        return _empty_prefill()

    d = prof.updated_at.date() if prof.updated_at else None
    return {
        "bust": prof.chest,
        "waist": prof.waist,
        "hips": prof.hip,
        "shoulder": prof.shoulder,
        "sleeve": prof.sleeve_length,
        "length": None,
        "inseam": prof.inseam,
        "neck": None,
        "notes": prof.notes,
        "from_order_date": d.isoformat() if d else None,
        "prefill_source": "profile",
        "recorded_at": prof.updated_at,
    }


def measurement_prefill_json_for_django(raw: dict[str, Any]) -> dict[str, Any]:
    """Strings for numeric fields, for JsonResponse in shop.views."""
    if not raw.get("from_order_date"):
        return {
            **_empty_measures(),
            "notes": None,
            "from_order_date": None,
            "prefill_source": None,
        }
    out = {
        k: str(raw[k]) if raw[k] is not None else None for k in _MEAS_KEYS
    }
    out["notes"] = raw["notes"]
    out["from_order_date"] = raw["from_order_date"]
    out["prefill_source"] = raw["prefill_source"]
    return out
