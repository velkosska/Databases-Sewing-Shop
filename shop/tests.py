from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from .models import Customer, Delivery, Order


class DeliveryRulesTest(TestCase):
    def test_delivered_order_requires_delivery_date(self):
        customer = Customer.objects.create(first_name="Test", last_name="Customer")
        order = Order.objects.create(customer=customer, due_date=date.today(), status=Order.Status.COMPLETED)
        delivery = Delivery(order=order, delivered=True, delivery_method=Delivery.Method.PICKUP)

        with self.assertRaises(ValidationError):
            delivery.save()

    def test_delivered_delivery_updates_order_status(self):
        customer = Customer.objects.create(first_name="Test", last_name="Customer")
        order = Order.objects.create(customer=customer, due_date=date.today(), status=Order.Status.COMPLETED)
        Delivery.objects.create(
            order=order,
            delivered=True,
            delivery_method=Delivery.Method.PICKUP,
            delivered_at=timezone.now(),
        )

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)
