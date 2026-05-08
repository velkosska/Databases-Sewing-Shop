"""One-time-ish backfill so Production logs is not empty after enabling the feature."""

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.formats import date_format as django_date_format

from shop.models import Delivery, OrderProductionLog, ProductionStage


def _fmt_local_dt(dt):
    if not dt:
        return ""
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return django_date_format(timezone.localtime(dt), format="SHORT_DATETIME_FORMAT")


def _as_aware(dt):
    if dt is None:
        return timezone.now()
    if timezone.is_naive(dt):
        return timezone.make_aware(dt, timezone.get_current_timezone())
    return timezone.localtime(dt)


class Command(BaseCommand):
    help = (
        "Create OrderProductionLog rows from existing ProductionStage and Delivery timestamps. "
        "Safe to run multiple times — skips rows already imported (payload.source=backfill)."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Show how many rows would be created without writing.",
        )

    def handle(self, *args, **options):
        dry = options["dry_run"]

        staged = list(
            ProductionStage.objects.select_related(
                "work_ticket__order_item__order"
            ).order_by("pk")
        )
        delivery_qs = Delivery.objects.select_related("order__customer")

        stages_start = stages_done = deli = skipped = 0

        objs: list[OrderProductionLog] = []

        def already(order, *, kind: str, match: dict) -> bool:
            q = {"order": order, "kind": kind, "payload__contains": match}
            return OrderProductionLog.objects.filter(**q).exists()

        for stage in staged:
            order = stage.work_ticket.order_item.order

            if stage.started_at:
                mark = {"stage_id": stage.pk, "ev": "start", "source": "backfill"}
                if already(order, kind=OrderProductionLog.Kind.STAGE_STARTED, match=mark):
                    skipped += 1
                else:
                    objs.append(
                        OrderProductionLog(
                            order_id=order.pk,
                            kind=OrderProductionLog.Kind.STAGE_STARTED,
                            created_at=_as_aware(stage.started_at),
                            payload={
                                "stage_name": stage.stage_name,
                                "at": _fmt_local_dt(stage.started_at),
                                **mark,
                            },
                        )
                    )
                    stages_start += 1

            if stage.completed_at:
                mark = {"stage_id": stage.pk, "ev": "complete", "source": "backfill"}
                if already(order, kind=OrderProductionLog.Kind.STAGE_COMPLETED, match=mark):
                    skipped += 1
                else:
                    objs.append(
                        OrderProductionLog(
                            order_id=order.pk,
                            kind=OrderProductionLog.Kind.STAGE_COMPLETED,
                            created_at=_as_aware(stage.completed_at),
                            payload={
                                "stage_name": stage.stage_name,
                                "at": _fmt_local_dt(stage.completed_at),
                                **mark,
                            },
                        )
                    )
                    stages_done += 1

        for d in delivery_qs:
            order = d.order
            mark = {"delivery_id": d.pk, "source": "backfill"}
            if already(order, kind=OrderProductionLog.Kind.DELIVERY, match=mark):
                skipped += 1
                continue
            method = d.delivery_method or ""
            at = _fmt_local_dt(d.delivered_at) if d.delivered_at else ""
            stamp = _as_aware(d.delivered_at) if d.delivered_at else timezone.now()
            objs.append(
                OrderProductionLog(
                    order_id=order.pk,
                    kind=OrderProductionLog.Kind.DELIVERY,
                    created_at=stamp,
                    payload={
                        "delivered": d.delivered,
                        "method": method,
                        "delivered_at": at,
                        **mark,
                    },
                )
            )
            deli += 1

        summary = (
            f"staging lines: started +{stages_start}, finished +{stages_done}; "
            f"delivery snapshots +{deli}; skipped (already backfilled): {skipped}; "
            f"would create total {len(objs)} log rows."
        )
        self.stdout.write(summary)

        if dry or not objs:
            return

        OrderProductionLog.objects.bulk_create(objs)
        self.stdout.write(self.style.SUCCESS(f"bulk_created {len(objs)} OrderProductionLog rows."))
