from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from orders.models import Order, Item, OrderItem
from revenue.models import Revenue
from revenue.tasks import RevenueUpdater


class RevenueViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.item = Item.objects.create(name='Товар', price=500)

    def create_paid_order_today(self, price=1000, quantity=2):
        order = Order.objects.create(
            table_number=1,
            status=Order.PAID,
            total_price=price,
            created_at=timezone.now()
        )
        OrderItem.objects.create(order=order, item=self.item, quantity=quantity)
        return order

    def test_revenue_list_view(self):
        # Предварительно создадим запись выручки
        Revenue.objects.create(amount=1234.56)
        response = self.client.get(reverse('revenue:revenue-data'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('revenues', response.context)
        self.assertIn('today', response.context)

    def test_create_revenue_view_success(self):
        self.create_paid_order_today(price=1500)

        response = self.client.post(reverse('revenue:revenue-create'), follow=True)
        self.assertEqual(response.status_code, 200)

        revenue = Revenue.objects.last()
        self.assertIsNotNone(revenue)
        self.assertEqual(revenue.amount, 1500)

    def test_create_revenue_view_no_paid_orders(self):
        response = self.client.post(reverse('revenue:revenue-create'), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Сегодня ещё нет оплаченных заказов.")
        self.assertEqual(Revenue.objects.count(), 0)

    def test_revenue_updater_creates_new_record(self):
        self.create_paid_order_today(price=999)
        result = RevenueUpdater.update_revenue()
        self.assertTrue(result)

        revenue = Revenue.objects.last()
        self.assertEqual(revenue.amount, 999)

    def test_revenue_updater_updates_existing_record(self):
        self.create_paid_order_today(price=500)
        Revenue.objects.create(amount=1000, created_at=timezone.now())

        # Новый заказ должен изменить сумму
        Order.objects.create(
            table_number=2,
            status=Order.PAID,
            total_price=250,
            created_at=timezone.now()
        )

        result = RevenueUpdater.update_revenue()
        self.assertTrue(result)

        updated = Revenue.objects.last()
        self.assertEqual(updated.amount, 750)

    def test_revenue_updater_no_paid_orders_returns_none(self):
        result = RevenueUpdater.update_revenue()
        self.assertIsNone(result)
        self.assertEqual(Revenue.objects.count(), 0)
