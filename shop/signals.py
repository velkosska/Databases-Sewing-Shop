from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.formats import date_format as django_date_format
from django.utils.translation import gettext as _

from .models import (
    Delivery,
    Order,
    OrderItem,
    OrderPayment,
    OrderProductionLog,
    ProductionStage,
    WorkTicket,
)
from .payment_sync import sync_order_payment_totals
from .production_logging import append_order_production_log
from .workflow_sync import refresh_order_aggregate_status


def _fmt_local_dt(dt):
    if not dt:
        return ""
    return django_date_format(timezone.localtime(dt), format="SHORT_DATETIME_FORMAT")


def _employee_label(employee_id):
    from .models import Employee

    if not employee_id:
        return ""
    emp = Employee.objects.filter(pk=employee_id).first()
    return emp.full_name if emp else str(employee_id)


@receiver(pre_save, sender=Order)
def order_pre_capture(sender, instance, **kwargs):
    instance._plog_prev_order = None
    if instance.pk:
        snap = Order.objects.filter(pk=instance.pk).values("status", "payment_status").first()
        if snap:
            instance._plog_prev_order = dict(snap)


@receiver(post_save, sender=Order)
def order_post_log(sender, instance, created, **kwargs):
    if created:
        return
    prev = getattr(instance, "_plog_prev_order", None)
    if not prev:
        return
    if prev.get("status") != instance.status:
        append_order_production_log(
            instance,
            OrderProductionLog.Kind.ORDER_STATUS,
            {"from": prev["status"], "to": instance.status},
        )
    if prev.get("payment_status") != instance.payment_status:
        append_order_production_log(
            instance,
            OrderProductionLog.Kind.PAYMENT_STATUS,
            {"from": prev["payment_status"], "to": instance.payment_status},
        )


@receiver(pre_save, sender=OrderItem)
def order_item_pre_capture(sender, instance, **kwargs):
    instance._plog_prev_item = None
    if instance.pk:
        snap = (
            OrderItem.objects.filter(pk=instance.pk)
            .values("status", "assigned_employee_id", "garment_type")
            .first()
        )
        if snap:
            instance._plog_prev_item = dict(snap)


@receiver(post_save, sender=OrderItem)
def order_item_post_log(sender, instance, created, **kwargs):
    if created:
        return
    prev = getattr(instance, "_plog_prev_item", None)
    if not prev:
        return
    order = instance.order
    garment = instance.garment_type or ""
    if prev.get("status") != instance.status:
        append_order_production_log(
            order,
            OrderProductionLog.Kind.ORDER_ITEM_STATUS,
            {
                "item_id": instance.pk,
                "garment": garment,
                "from": prev["status"],
                "to": instance.status,
            },
        )
    peid = prev.get("assigned_employee_id")
    neid = instance.assigned_employee_id
    if peid != neid:
        append_order_production_log(
            order,
            OrderProductionLog.Kind.ORDER_ITEM_ASSIGNED,
            {
                "item_id": instance.pk,
                "garment": garment,
                "from_employee": _employee_label(peid) or _("Unassigned"),
                "to_employee": _employee_label(neid) or _("Unassigned"),
            },
        )


@receiver(pre_save, sender=WorkTicket)
def workticket_pre_capture(sender, instance, **kwargs):
    instance._plog_prev_ticket = None
    if instance.pk:
        snap = WorkTicket.objects.filter(pk=instance.pk).values(
            "status", "assigned_to_id"
        ).first()
        if snap:
            instance._plog_prev_ticket = dict(snap)


@receiver(post_save, sender=WorkTicket)
def workticket_post_log_and_sync(sender, instance, created, **kwargs):
    if not created:
        prev = getattr(instance, "_plog_prev_ticket", None)
        if prev:
            order = instance.order_item.order
            garment = instance.order_item.garment_type or ""
            if prev.get("status") != instance.status:
                append_order_production_log(
                    order,
                    OrderProductionLog.Kind.TICKET_STATUS,
                    {
                        "ticket_id": instance.pk,
                        "garment": garment,
                        "from": prev["status"],
                        "to": instance.status,
                    },
                )
            pid = prev.get("assigned_to_id")
            nid = instance.assigned_to_id
            if pid != nid:
                append_order_production_log(
                    order,
                    OrderProductionLog.Kind.TICKET_ASSIGNED,
                    {
                        "ticket_id": instance.pk,
                        "garment": garment,
                        "from_employee": _employee_label(pid) or _("Unassigned"),
                        "to_employee": _employee_label(nid) or _("Unassigned"),
                    },
                )
    refresh_order_aggregate_status(instance.order_item.order)


@receiver(pre_save, sender=ProductionStage)
def stage_pre_capture(sender, instance, **kwargs):
    instance._plog_prev_stage = None
    if instance.pk:
        snap = ProductionStage.objects.filter(pk=instance.pk).values(
            "started_at", "completed_at", "stage_name"
        ).first()
        if snap:
            instance._plog_prev_stage = dict(snap)


@receiver(post_save, sender=ProductionStage)
def stage_post_log(sender, instance, created, **kwargs):
    order = instance.work_ticket.order_item.order
    sn = instance.stage_name
    if created:
        if instance.started_at:
            append_order_production_log(
                order,
                OrderProductionLog.Kind.STAGE_STARTED,
                {"stage_name": sn, "at": _fmt_local_dt(instance.started_at)},
            )
        if instance.completed_at:
            append_order_production_log(
                order,
                OrderProductionLog.Kind.STAGE_COMPLETED,
                {"stage_name": sn, "at": _fmt_local_dt(instance.completed_at)},
            )
        return
    prev = getattr(instance, "_plog_prev_stage", None) or {}
    old_s, new_s = prev.get("started_at"), instance.started_at
    if old_s != new_s and new_s is not None:
        append_order_production_log(
            order,
            OrderProductionLog.Kind.STAGE_STARTED,
            {"stage_name": sn, "at": _fmt_local_dt(new_s)},
        )
    old_c, new_c = prev.get("completed_at"), instance.completed_at
    if old_c != new_c and new_c is not None:
        append_order_production_log(
            order,
            OrderProductionLog.Kind.STAGE_COMPLETED,
            {"stage_name": sn, "at": _fmt_local_dt(new_c)},
        )


@receiver(pre_save, sender=Delivery)
def delivery_pre_capture(sender, instance, **kwargs):
    instance._plog_prev_delivery = None
    if instance.pk:
        snap = Delivery.objects.filter(pk=instance.pk).values(
            "delivered", "delivered_at", "delivery_method"
        ).first()
        if snap:
            instance._plog_prev_delivery = dict(snap)


@receiver(post_save, sender=Delivery)
def delivery_post_log(sender, instance, created, **kwargs):
    order = instance.order
    method = instance.delivery_method or ""
    at = _fmt_local_dt(instance.delivered_at) if instance.delivered_at else ""
    if created:
        append_order_production_log(
            order,
            OrderProductionLog.Kind.DELIVERY,
            {
                "delivered": instance.delivered,
                "method": method,
                "delivered_at": at,
            },
        )
        return
    prev = getattr(instance, "_plog_prev_delivery", None) or {}
    if (
        prev.get("delivered") != instance.delivered
        or prev.get("delivered_at") != instance.delivered_at
        or prev.get("delivery_method") != instance.delivery_method
    ):
        append_order_production_log(
            order,
            OrderProductionLog.Kind.DELIVERY,
            {
                "delivered": instance.delivered,
                "method": method,
                "delivered_at": at,
            },
        )


@receiver(post_save, sender=OrderPayment)
@receiver(post_delete, sender=OrderPayment)
def payment_sync_order_totals(sender, instance, **kwargs):
    sync_order_payment_totals(instance.order_id)
