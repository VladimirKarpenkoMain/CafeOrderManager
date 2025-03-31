from rest_framework import generics, status
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.views import APIView
from orders.models import Order, Item
from api.serializers import (
    OrderSerializer, CreateOrderSerializer,
    UpdateOrderStatusSerializer, ItemSerializer, RevenueSerializer
)
from django.shortcuts import get_object_or_404

from revenue.models import Revenue
from revenue.tasks import RevenueUpdater


class ItemListView(generics.ListAPIView):
    """
    Представление для получения списка товаров.
    Возвращает список всех доступных товаров.
    """
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class OrderListCreateView(generics.ListCreateAPIView):
    """
    Список заказов (GET) и создание нового заказа (POST).

    GET: Возвращает список заказов с возможностью фильтрации по номеру стола,
    дате и статусу. Также поддерживает пагинацию.

    POST: Создает новый заказ на основе данных, переданных в запросе.
    """
    queryset = Order.objects.prefetch_related(
        'orderitem_set__item'
    ).order_by('-created_at')

    pagination_class = PageNumberPagination  # Включает пагинацию

    def get_serializer_class(self):
        """
        Определяет, какой сериализатор использовать в зависимости от метода запроса.
        """
        if self.request.method == 'POST':
            return CreateOrderSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        """
        Создает новый заказ.

        Проверяет валидность переданных данных, сохраняет заказ в базе данных
        и возвращает данные нового заказа.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)  # Проверяем данные
        order = serializer.save()  # Сохраняем заказ

        # Возвращаем сериализованные данные созданного заказа
        read_serializer = OrderSerializer(order)
        return Response(read_serializer.data, status=status.HTTP_201_CREATED)

    def get_queryset(self):
        """
        Применяет фильтрацию к запросу списка заказов.

        Поиск:
        - По номеру стола (параметр `search`).

        Фильтры:
        - По дате создания заказа (параметр `date`).
        - По статусу заказа (параметр `status`).
        """
        queryset = super().get_queryset()

        # Фильтрация по номеру стола
        search_query = self.request.query_params.get('search', '')
        if search_query:
            queryset = queryset.filter(table_number__icontains=search_query)

        # Фильтрация по дате и статусу
        date = self.request.query_params.get('date')
        status = self.request.query_params.get('status')
        if date:
            queryset = queryset.filter(created_at__date=date)
        if status:
            queryset = queryset.filter(status=status)

        return queryset


class UpdateOrderStatusView(APIView):
    """
    Представление для обновления статуса заказа.

    PATCH: Позволяет частично обновить статус заказа по его ID.
    """

    def patch(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)  # Получаем заказ

        # Проверяем, можно ли обновлять статус
        if order.status == Order.PAID:
            return Response(
                {"detail": "Нельзя изменить статус оплаченного заказа."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Применяем изменения статуса
        serializer = UpdateOrderStatusSerializer(order, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()  # Сохраняем изменения
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteOrderView(APIView):
    """
    Представление для удаления заказа.

    DELETE: Удаляет заказ, если он не имеет статуса "оплачен" или "выполнен".
    """

    def delete(self, request, order_id):
        order = get_object_or_404(Order, id=order_id)  # Получаем заказ

        # Проверяем статус заказа перед удалением
        if order.status in (Order.PAID, Order.DONE):
            return Response(
                {"detail": f"Нельзя удалить заказ с ID {order_id}. Он уже оплачен или выполнен."},
                status=status.HTTP_403_FORBIDDEN
            )

        order.delete()  # Удаляем заказ
        return Response(
            {"detail": f"Заказ с ID {order_id} успешно удален."},
            status=status.HTTP_200_OK
        )

class RevenueListView(generics.ListAPIView):
    """
    Возвращает список всех записей выручки, сортируя по дате по убыванию.
    """
    queryset = Revenue.objects.all().order_by('-created_at')
    serializer_class = RevenueSerializer

class UpdateRevenueView(APIView):
    """
    POST /api/revenue/update/
    Вызывает RevenueUpdater.update_revenue()
    """
    def post(self, request, *args, **kwargs):
        result = RevenueUpdater.update_revenue()

        if result is None:
            # Нет оплаченных заказов за сегодня
            return Response(
                {"detail": "No paid orders found for today."},
                status=status.HTTP_200_OK
            )
        elif result is False:
            # Произошла ошибка во время обновления
            return Response(
                {"detail": "Error during revenue update."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        else:
            # Успешное обновление
            return Response(
                {"detail": "Revenue updated successfully."},
                status=status.HTTP_200_OK
            )