from datetime import date

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Customer, Delivery, Order


class DeliveryRulesTest(TestCase):
    def test_delivered_order_requires_delivery_date(self):
        customer = Customer.objects.create(full_name="Test Customer")
        order = Order.objects.create(customer=customer, status=Order.Status.COMPLETED)
        delivery = Delivery(order=order, delivered=True, method=Delivery.Method.PICKUP)

        with self.assertRaises(ValidationError):
            delivery.save()

    def test_delivered_delivery_updates_order_status(self):
        customer = Customer.objects.create(full_name="Test Customer")
        order = Order.objects.create(customer=customer, status=Order.Status.COMPLETED)
        Delivery.objects.create(
            order=order,
            delivered=True,
            method=Delivery.Method.PICKUP,
            delivery_date=date.today(),
        )

        order.refresh_from_db()
        self.assertEqual(order.status, Order.Status.DELIVERED)
