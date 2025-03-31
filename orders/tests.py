from django.test import TestCase, Client
from django.urls import reverse
from orders.models import Order, OrderItem, Item
from django.utils import timezone


class OrderViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.item = Item.objects.create(name='Пицца', price=300)

    def create_order(self, status=Order.WAITING, table_number=5):
        order = Order.objects.create(
            status=status,
            total_price=600,
            table_number=table_number,
        )
        OrderItem.objects.create(order=order, item=self.item, quantity=2)
        return order

    def test_order_list_view(self):
        order = self.create_order()
        url = reverse('orders:order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(order, response.context['orders'])

    def test_order_search_by_table(self):
        order = self.create_order(table_number=42)
        url = reverse('orders:order-list') + '?search=42'
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertIn(order, response.context['orders'])

    def test_order_filter_by_date_and_status(self):
        order = self.create_order(status=Order.DONE)
        order.created_at = timezone.now()
        order.save()
        url = reverse('orders:order-list')
        response = self.client.get(url, {
            'status': Order.DONE,
            'date': order.created_at.date()
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn(order, response.context['orders'])

    def test_create_order_view(self):
        url = reverse('orders:order-create')
        response = self.client.post(url, {
            'items': [self.item.id],
            f'quantity_id_items_{self.item.id - 1}': 2,
            'table_number': 7
        })
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.total_price, 600)

    def test_update_order_status(self):
        order = self.create_order(status=Order.WAITING)
        url = reverse('orders:status-update', kwargs={'order_id': order.id})
        response = self.client.post(url, {'status': Order.DONE})
        self.assertRedirects(response, reverse('orders:order-list'))
        order.refresh_from_db()
        self.assertEqual(order.status, Order.DONE)

    def test_cannot_update_paid_order(self):
        order = self.create_order(status=Order.PAID)
        url = reverse('orders:status-update', kwargs={'order_id': order.id})
        response = self.client.post(url, {'status': Order.DONE})
        self.assertEqual(response.status_code, 403)

    def test_delete_order_success(self):
        order = self.create_order()
        url = reverse('orders:order-delete')
        response = self.client.post(url, {'order_id': order.id})
        self.assertRedirects(response, reverse('orders:order-list'))
        self.assertFalse(Order.objects.filter(id=order.id).exists())

    def test_cannot_delete_paid_order(self):
        order = self.create_order(status=Order.PAID)
        url = reverse('orders:order-delete')
        response = self.client.post(url, {'order_id': order.id}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Order.objects.filter(id=order.id).exists())
