from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, FormView
from django.db.models import Prefetch, Q

from orders.filters import OrdersFilterForm
from orders.models import Order, OrderItem
from orders.forms import OrderCreateForm, StatusUpdateForm, DeleteOrderForm
from common.mixins import TitleMixin


class OrdersView(TitleMixin, ListView):
    """
    Отображает список заказов с пагинацией и поддержкой фильтрации и поиска.
    """
    model = Order
    template_name = 'orders/order_list.html'
    context_object_name = 'orders'
    title = "Заказы"
    paginate_by = settings.PAGINATION_ORDERS_LIST_VIEW

    def get_form(self):
        return OrdersFilterForm(self.request.GET)

    def get_base_queryset(self):
        return self.model.objects.all().prefetch_related(
            Prefetch(
                'orderitem_set',
                queryset=OrderItem.objects.select_related('item'),
                to_attr='prefetched_order_items'
            )
        ).order_by('-created_at')

    def apply_search_filter(self, queryset):
        """
        Ищет заказы по номеру стола.
        """
        search_query = self.request.GET.get('search', '')
        matching_status_codes = [
            code for code, label in Order.STATUSES
            if search_query in label.lower()
        ]

        if search_query:
            return queryset.filter(
                Q(table_number__icontains=search_query) | Q(status__in=matching_status_codes)
            )
        return queryset

    def apply_form_filters(self, queryset):
        """
        Применяет фильтры из формы (дата и статус) к запросу
        """
        form = self.get_form()
        if form.is_valid():
            filters = {}
            date = form.cleaned_data.get('date')
            status = form.cleaned_data.get('status')
            if date:
                filters['created_at__date'] = date
            if status:
                filters['status'] = status
            if filters:
                queryset = queryset.filter(**filters)
        return queryset

    def get_queryset(self):
        queryset = self.get_base_queryset()
        queryset = self.apply_search_filter(queryset)
        queryset = self.apply_form_filters(queryset)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = self.get_form()
        return context


class CreateOrderView(TitleMixin, CreateView):
    """
    Обрабатывает создание заказа.
    """
    model = Order
    form_class = OrderCreateForm
    template_name = 'orders/order_create.html'
    success_url = reverse_lazy('orders:order-list')
    title = "Создание заказа"

    def form_valid(self, form):
        """
        Проверяет форму, рассчитывает общую стоимость заказа и создает объекты through таблицы.
        """
        self.object = form.save(commit=False)

        # Получение товаров и их количества
        items = form.cleaned_data['items']
        order_items = []
        for item in items:
            quantity = int(self.request.POST.get(f'quantity_id_items_{item.id-1}'))
            order_items.append(OrderItem(order=self.object, item=item, quantity=quantity))

        # Расчет общей стоимости
        total_price = sum([order_item.item.price * order_item.quantity for order_item in order_items])
        self.object.total_price = total_price
        self.object.save()

        # Массовое создание объектов OrderItem
        OrderItem.objects.bulk_create(order_items)

        return super().form_valid(form)


class UpdateOrderView(TitleMixin, UpdateView):
    """
    Обновляет статус заказа. Не позволяет изменить статус, если заказ уже оплачен.
    """
    model = Order
    template_name = 'orders/order_update_status.html'
    form_class = StatusUpdateForm
    success_url = reverse_lazy('orders:order-list')
    pk_url_kwarg = 'order_id'
    title = "Обновление статуса заказа"

    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
        if obj.status == Order.PAID:
            return HttpResponseForbidden("Данный заказ уже был оплачен и изменить его статус нельзя!")
        return super().dispatch(request, *args, **kwargs)


class DeleteFormView(TitleMixin, FormView):
    """
    Обрабатывает удаление заказа.
    """
    template_name = 'orders/order_delete.html'
    form_class = DeleteOrderForm
    success_url = reverse_lazy('orders:order-list')
    title = "Удаление заказа"

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            order_id = form.cleaned_data['order_id']
            try:
                order = get_object_or_404(Order, id=order_id)
                if order.status in (Order.PAID, Order.DONE):
                    messages.info(request, f'Заказ с ID {order_id} уже оплачен или готов! Его нельзя удалить.')
                    return redirect('orders:order-delete')
                order.delete()
                messages.success(request, f'Заказ с ID {order_id} успешно удален.')
            except Exception as e:
                messages.error(request, f'Заказ с ID {order_id} не найден.')
                return redirect('orders:order-delete')
            return redirect(self.success_url)
        else:
            messages.error(request, 'Некорректный ID заказа.')
            return self.render_to_response({'form': form})
