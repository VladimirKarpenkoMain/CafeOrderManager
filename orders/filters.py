from django import forms
from orders.models import Order


class OrdersFilterForm(forms.Form):
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'placeholder': 'Дата'}),
        label="Дата"
    )
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Все'),
            (Order.WAITING, 'В ожидании'),
            (Order.DONE, 'Готово'),
            (Order.PAID, 'Оплачено')
        ],
        label="Статус"
    )