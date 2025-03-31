from django import forms
from .models import Order, Item

class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['table_number', 'items']

    items = forms.ModelMultipleChoiceField(
            label="Блюда",
            queryset=Item.objects.all(),
            widget=forms.CheckboxSelectMultiple(attrs={'class': 'dish-checkbox'}),
            required=True,
        )

    table_number = forms.IntegerField(
        label="Номер стола",
        min_value=1,
        max_value=100,
        widget=forms.TextInput(
            attrs={
            'class': 'form-control table-number',
            'placeholder': 'Введите номер стола'
            }
        )
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Переопределяем метки для объектов `items`
        self.fields['items'].label_from_instance = lambda obj: obj.name

class StatusUpdateForm(forms.ModelForm):
    status = forms.ChoiceField(
        choices=Order.STATUSES,
        label="Выберите статус",
        widget=forms.Select
    )
    class Meta:
        model = Order
        fields = ['status']

class DeleteOrderForm(forms.Form):
    order_id = forms.IntegerField(label="Введите ID заказа")