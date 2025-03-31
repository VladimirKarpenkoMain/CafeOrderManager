from django.db import models
from django.core.validators import MaxValueValidator

class Item(models.Model):
    name = models.CharField(max_length=128)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Item(name="{self.name}", price={self.price})'

class Order(models.Model):
    WAITING = 0
    DONE = 1
    PAID = 2

    STATUSES = (
        (WAITING, 'В ожидании'),
        (DONE, 'Готово'),
        (PAID, 'Оплачено'),
    )

    table_number = models.PositiveIntegerField(validators=[MaxValueValidator(100)])
    items = models.ManyToManyField(Item, through='OrderItem')
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.SmallIntegerField(default=WAITING, choices=STATUSES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Order #{self.id}: Table {self.table_number}, Total Price: {self.total_price}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'OrderItem(Order #{self.order.id}, Item={self.item.name}, Quantity={self.quantity})'
