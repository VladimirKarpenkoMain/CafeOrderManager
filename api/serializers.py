from rest_framework import serializers
from orders.models import Order, OrderItem, Item
from revenue.models import Revenue


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = ['id', 'name', 'price']


class OrderItemSerializer(serializers.ModelSerializer):
    item_id = serializers.PrimaryKeyRelatedField(queryset=Item.objects.all(), source='item')
    name = serializers.CharField(source='item.name', read_only=True)
    price = serializers.DecimalField(source='item.price', read_only=True, max_digits=10, decimal_places=2)

    class Meta:
        model = OrderItem
        fields = ['item_id', 'name', 'price', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(source='orderitem_set', many=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ['id', 'table_number', 'items', 'total_price', 'status', 'status_display', 'created_at']

class CreateOrderItemSerializer(serializers.ModelSerializer):
    item_id = serializers.PrimaryKeyRelatedField(
        queryset=Item.objects.all(),
        source='item'
    )
    quantity = serializers.IntegerField(min_value=1, max_value=100)

    class Meta:
        model = OrderItem
        fields = ['item_id', 'quantity']

class CreateOrderSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания заказа.
    """
    items = CreateOrderItemSerializer(many=True)  # Список позиций заказа
    table_number = serializers.IntegerField(min_value=1, max_value=100)

    class Meta:
        model = Order
        fields = ['table_number', 'items']

    def create(self, validated_data):
        """
        Создаем заказ и связанные с ним позиции.
        """
        items_data = validated_data.pop('items')  # Удаляем данные о товарах из общего словаря
        order = Order.objects.create(**validated_data)

        # Создаем позиции заказа
        order_items = [
            OrderItem(order=order, **item_data) for item_data in items_data
        ]
        OrderItem.objects.bulk_create(order_items)

        # Пересчитываем общую стоимость заказа
        total_price = sum(order_item.item.price * order_item.quantity for order_item in order_items)
        order.total_price = total_price
        order.save()

        return order


class UpdateOrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ['status']

class RevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revenue
        fields = ['id', 'amount', 'created_at']
        read_only_fields = ['id', 'created_at']
