from rest_framework.test import APITestCase
from rest_framework import status
from django.urls import reverse
from orders.models import Order, Item, OrderItem
from revenue.models import Revenue
from django.utils import timezone


class APITestViews(APITestCase):
    def setUp(self):
        self.item1 = Item.objects.create(name="Кофе", price=150)
        self.item2 = Item.objects.create(name="Пицца", price=500)

    def create_order(self, status=Order.WAITING, total_price=1000):
        order = Order.objects.create(
            table_number=1,
            status=status,
            total_price=total_price,
            created_at=timezone.now()
        )
        OrderItem.objects.create(order=order, item=self.item1, quantity=2)
        return order

    def test_item_list_view(self):
        url = reverse('api:item-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 4)

    def test_order_list_view(self):
        self.create_order()
        url = reverse('api:order-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_order_create_view(self):
        url = reverse('api:order-list')
        data = {
            "table_number": 10,
            "items": [
                {"item_id": self.item1.id, "quantity": 1},
                {"item_id": self.item2.id, "quantity": 2}
            ]
        }
        response = self.client.post(url, data, format='json')

        if response.status_code != 201:
            print("Ошибка:", response.data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(OrderItem.objects.count(), 2)

        order = Order.objects.first()
        expected_total = self.item1.price * 1 + self.item2.price * 2
        self.assertEqual(order.total_price, expected_total)

    def test_order_list_filter_by_table(self):
        self.create_order()
        url = reverse('api:order-list') + '?search=1'
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)

    def test_update_order_status_success(self):
        order = self.create_order()
        url = reverse('api:order-update-status', args=[order.id])
        response = self.client.patch(url, {"status": Order.DONE}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        order.refresh_from_db()
        self.assertEqual(order.status, Order.DONE)

    def test_update_order_status_forbidden(self):
        order = self.create_order(status=Order.PAID)
        url = reverse('api:order-update-status', args=[order.id])
        response = self.client.patch(url, {"status": Order.DONE}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_delete_order_success(self):
        order = self.create_order()
        url = reverse('api:order-delete', args=[order.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Order.objects.filter(id=order.id).exists())

    def test_delete_order_forbidden(self):
        order = self.create_order(status=Order.PAID)
        url = reverse('api:order-delete', args=[order.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Order.objects.filter(id=order.id).exists())

    def test_revenue_list_view(self):
        Revenue.objects.create(amount=5000)
        url = reverse('api:revenues-list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_update_revenue_no_paid_orders(self):
        url = reverse('api:revenue-update')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "No paid orders found for today.")

    def test_update_revenue_success(self):
        self.create_order(status=Order.PAID, total_price=1200)
        url = reverse('api:revenue-update')
        response = self.client.post(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["detail"], "Revenue updated successfully.")
        self.assertEqual(Revenue.objects.last().amount, 1200)
