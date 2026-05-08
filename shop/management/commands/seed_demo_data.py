from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from shop.models import (
    Catalogue,
    Customer,
    Delivery,
    Employee,
    Material,
    Measurement,
    Order,
    OrderItem,
    OrderItemMaterial,
    ProductionStage,
    WorkTicket,
)
from shop.production_logging import pause_order_production_logs


class Command(BaseCommand):
    help = "Populate the database with complete demo data for all core models."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete existing shop data first, then reseed from scratch.",
        )
        parser.add_argument(
            "--orders",
            type=int,
            default=80,
            help="How many orders to generate (default: 80).",
        )
        parser.add_argument(
            "--extra-customers",
            type=int,
            default=30,
            help="How many synthetic customers to ensure in total generation set (default: 30).",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        with pause_order_production_logs():
            self._seed_body(options)

    def _seed_body(self, options):
        if options["reset"]:
            self._reset_data()

        today = date.today()
        total_orders = max(20, options["orders"])
        synthetic_customers = max(20, options["extra_customers"])

        first_names = [
            "Maria", "Carlos", "Ana", "Pedro", "Laura", "Lucia", "Jorge", "Sofia", "Miguel", "Elena",
            "Diego", "Nora", "Alba", "Pablo", "Irene", "Sara", "Hugo", "Mateo", "Clara", "Daniel",
        ]
        last_names = [
            "Garcia", "Lopez", "Martinez", "Fernandez", "Sanchez", "Ramos", "Diaz", "Torres", "Ruiz", "Vega",
            "Navarro", "Ortega", "Castro", "Molina", "Suarez", "Gil", "Iglesias", "Benitez", "Prieto", "Calvo",
        ]
        customers = []
        for idx in range(synthetic_customers):
            first_name = first_names[idx % len(first_names)]
            last_name = last_names[(idx * 3) % len(last_names)]
            customers.append(
                {
                    "first_name": first_name,
                    "last_name": last_name,
                    "phone": f"6{idx:08d}"[:9],
                    "email": f"{first_name.lower()}.{last_name.lower()}{idx}@email.com",
                }
            )

        for payload in customers:
            customer, _ = Customer.objects.get_or_create(
                first_name=payload["first_name"],
                last_name=payload["last_name"],
                defaults={
                    "phone": payload["phone"],
                    "email": payload["email"],
                    "address": "Spain",
                    "notes": "Seeded customer",
                },
            )
            Measurement.objects.get_or_create(
                customer=customer,
                defaults={
                    "chest": Decimal("90.00"),
                    "waist": Decimal("70.00"),
                    "hip": Decimal("95.00"),
                    "shoulder": Decimal("40.00"),
                    "sleeve_length": Decimal("60.00"),
                    "inseam": Decimal("78.00"),
                },
            )

        employees = [
            ("Lucia", "Ramos", "Tailor"),
            ("Jorge", "Diaz", "Cutter"),
            ("Sofia", "Torres", "Finisher"),
            ("Miguel", "Ruiz", "Tailor"),
        ]
        for first_name, last_name, role in employees:
            Employee.objects.get_or_create(
                first_name=first_name,
                last_name=last_name,
                defaults={"role": role, "notes": "Seeded employee"},
            )

        # Expanded catalogue set for richer demos and reporting.
        catalogue_items = [
            ("Wedding Dress Tailoring", Decimal("350.00")),
            ("Formal Suit Tailoring", Decimal("280.00")),
            ("Summer Dress Sewing", Decimal("90.00")),
            ("Trousers Tailoring", Decimal("110.00")),
            ("Bridesmaid Dress Sewing", Decimal("180.00")),
            ("Evening Gown Tailoring", Decimal("320.00")),
            ("Office Blazer Tailoring", Decimal("220.00")),
            ("School Uniform Set", Decimal("160.00")),
            ("Custom Shirt Tailoring", Decimal("95.00")),
            ("Traditional Dress Sewing", Decimal("260.00")),
            ("Coat Alteration", Decimal("85.00")),
            ("Jeans Alteration", Decimal("45.00")),
            ("Skirt Alteration", Decimal("40.00")),
            ("Jacket Repair", Decimal("55.00")),
            ("Curtain Sewing Service", Decimal("130.00")),
        ]
        catalogues = {}
        for service, base_price in catalogue_items:
            obj, _ = Catalogue.objects.get_or_create(service=service, defaults={"base_price": base_price})
            catalogues[service] = obj

        # Backfill measurements for all existing customers, including pre-seeded/manual records.
        for idx, customer in enumerate(Customer.objects.order_by("id")):
            Measurement.objects.get_or_create(
                customer=customer,
                defaults={
                    "chest": Decimal("88.00") + Decimal(idx % 12),
                    "waist": Decimal("68.00") + Decimal(idx % 10),
                    "hip": Decimal("92.00") + Decimal(idx % 11),
                    "shoulder": Decimal("38.00") + Decimal(idx % 6),
                    "sleeve_length": Decimal("58.00") + Decimal(idx % 7),
                    "inseam": Decimal("75.00") + Decimal(idx % 8),
                    "notes": "Auto-generated baseline measurements",
                },
            )

        materials = [
            ("Premium Denim", "Blue", Decimal("12.50"), Decimal("45.50")),
            ("White Cotton", "White", Decimal("6.00"), Decimal("80.00")),
            ("Red Silk", "Red", Decimal("22.00"), Decimal("20.00")),
            ("Black Thread", "Black", Decimal("0.80"), Decimal("100.00")),
            ("White Zipper", "White", Decimal("1.20"), Decimal("60.00")),
        ]
        material_map = {}
        for name, color, unit_price, stock_quantity in materials:
            obj, _ = Material.objects.get_or_create(
                name=name,
                color=color,
                defaults={"unit_price": unit_price, "stock_quantity": stock_quantity},
            )
            material_map[name] = obj

        customer_list = list(Customer.objects.order_by("id"))
        employee_list = list(Employee.objects.order_by("id"))
        catalogue_list = list(Catalogue.objects.order_by("id"))
        material_list = list(Material.objects.order_by("id"))

        garment_templates = [
            ("Wedding Dress", "White", Decimal("380.00"), "Lace sleeves, long train"),
            ("Formal Suit", "Navy", Decimal("560.00"), "Classic cut, two buttons"),
            ("Summer Dress", "Floral", Decimal("95.00"), "A-line, pockets"),
            ("Casual Trousers", "Khaki", Decimal("115.00"), "Straight leg"),
            ("Bridesmaid Dress", "Dusty Rose", Decimal("185.00"), "Knee length satin"),
            ("Blazer", "Black", Decimal("210.00"), "Slim fit"),
            ("Skirt", "Green", Decimal("125.00"), "Pleated style"),
            ("Shirt", "White", Decimal("90.00"), "French cuffs"),
            ("Evening Gown", "Burgundy", Decimal("340.00"), "Open back, beaded waist"),
            ("School Uniform", "Navy", Decimal("165.00"), "2 shirts + 2 trousers"),
            ("Custom Jacket", "Charcoal", Decimal("245.00"), "Water-resistant lining"),
            ("Curtain Set", "Ivory", Decimal("145.00"), "Living room 2-panel set"),
        ]

        priority_cycle = [
            WorkTicket.Priority.URGENT,
            WorkTicket.Priority.HIGH,
            WorkTicket.Priority.NORMAL,
            WorkTicket.Priority.LOW,
        ]
        status_cycle = [
            Order.Status.PENDING,
            Order.Status.IN_PRODUCTION,
            Order.Status.PENDING,
            Order.Status.COMPLETED,
            Order.Status.DELIVERED,
        ]

        for idx in range(total_orders):
            customer = customer_list[idx % len(customer_list)]
            order_status = status_cycle[idx % len(status_cycle)]
            due_in_days = (idx % 36) - 10  # Mix overdue and future.
            order_note = f"Seeded order batch #{idx + 1}"
            order = Order.objects.create(
                customer=customer,
                due_date=today + timedelta(days=due_in_days),
                status=order_status,
                notes=order_note,
                total_price=Decimal("0.00"),
            )

            # Spread order dates across the past ~60 days.
            Order.objects.filter(pk=order.pk).update(order_date=today - timedelta(days=(idx % 60)))
            order.refresh_from_db(fields=["order_date"])

            template = garment_templates[idx % len(garment_templates)]
            catalogue = catalogue_list[idx % len(catalogue_list)]
            quantity = 1 + (idx % 3)
            final_price = template[2] + Decimal(str((idx % 7) * 5))
            item_status = "pending" if order_status == Order.Status.PENDING else "in_progress"
            if order_status in (Order.Status.COMPLETED, Order.Status.DELIVERED):
                item_status = "completed"

            item = OrderItem.objects.create(
                order=order,
                catalogue=catalogue,
                garment_type=template[0],
                quantity=quantity,
                color=template[1],
                design_notes=template[3],
                status=item_status,
                final_price=final_price,
            )

            assigned_employee = employee_list[idx % len(employee_list)]
            ticket_status = WorkTicket.Status.PENDING
            if order_status == Order.Status.IN_PRODUCTION:
                ticket_status = WorkTicket.Status.IN_PROGRESS
            elif order_status in (Order.Status.COMPLETED, Order.Status.DELIVERED):
                ticket_status = WorkTicket.Status.DONE

            ticket = WorkTicket.objects.create(
                order_item=item,
                assigned_to=assigned_employee,
                priority=priority_cycle[idx % len(priority_cycle)],
                status=ticket_status,
                deadline=order.due_date,
                notes=f"Ticket for order #{order.id}",
                created_at=timezone.now() - timedelta(days=(idx % 20)),
            )

            stage_names = [
                ProductionStage.StageName.ORDER_RECEIVED,
                ProductionStage.StageName.CUTTING,
                ProductionStage.StageName.SEWING,
            ]
            if order_status in (Order.Status.COMPLETED, Order.Status.DELIVERED):
                stage_names.append(ProductionStage.StageName.QUALITY_CHECK)
            for s_idx, stage_name in enumerate(stage_names):
                ProductionStage.objects.create(
                    work_ticket=ticket,
                    stage_name=stage_name,
                    started_at=timezone.now() - timedelta(days=max(0, 4 - s_idx)),
                )

            m1 = material_list[idx % len(material_list)]
            m2 = material_list[(idx + 2) % len(material_list)]
            OrderItemMaterial.objects.get_or_create(
                order_item=item,
                material=m1,
                defaults={"quantity_used": Decimal("1.50") + Decimal(str(idx % 3))},
            )
            if m2.id != m1.id:
                OrderItemMaterial.objects.get_or_create(
                    order_item=item,
                    material=m2,
                    defaults={"quantity_used": Decimal("0.80") + Decimal(str((idx + 1) % 2))},
                )

            order.total_price = (item.final_price or Decimal("0")) * item.quantity
            order.save(update_fields=["total_price"])

            if order.status in (Order.Status.COMPLETED, Order.Status.DELIVERED):
                Delivery.objects.get_or_create(
                    order=order,
                    defaults={
                        "delivered_at": timezone.now() - timedelta(days=idx % 5),
                        "delivery_method": Delivery.Method.PICKUP if idx % 2 == 0 else Delivery.Method.COURIER,
                        "recipient_name": customer.full_name,
                        "delivered": order.status == Order.Status.DELIVERED,
                        "comments": "Auto-seeded delivery record",
                    },
                )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data seeded successfully with {total_orders} orders and varied priorities/dates."
            )
        )

    def _reset_data(self):
        Delivery.objects.all().delete()
        ProductionStage.objects.all().delete()
        WorkTicket.objects.all().delete()
        OrderItemMaterial.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        Measurement.objects.all().delete()
        Material.objects.all().delete()
        Catalogue.objects.all().delete()
        Employee.objects.all().delete()
        Customer.objects.all().delete()

