from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.views.generic import ListView, View
from django.utils import timezone
from common.mixins import TitleMixin

from revenue.models import Revenue
from revenue.tasks import RevenueUpdater


class RevenueView(TitleMixin, ListView):
    """
    Отображает данные о выручке за оплаченные заказы.
    """
    template_name = 'revenue/revenue_data.html'
    title = 'Выручка за оплаченные заказы'
    paginate_by = settings.PAGINATION_ORDERS_LIST_VIEW

    def get_queryset(self):
        return Revenue.objects.all().order_by('-created_at')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        queryset = self.get_queryset()

        today = timezone.now()

        # Получение данных о выручке за текущий день
        today_revenue = queryset.filter(
            created_at__date=today.date()
        ).last()  # Последняя запись за сегодня

        if today_revenue:
            context['amount'] = today_revenue.amount
            context['update_time'] = today_revenue.created_at

        # Добавление списка всех записей о выручке и текущей даты в контекст
        context['revenues'] = queryset
        context['today'] = today

        return context


class CreateRevenueView(View):
    """
    Обрабатывает запрос на создание или обновление выручки.
    """
    def post(self, request, *args, **kwargs):
        revenue = RevenueUpdater.update_revenue()

        if revenue is None:
            # Если на текущий день нет оплаченных заказов
            messages.info(request, "Сегодня ещё нет оплаченных заказов.")
            return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

        if revenue:
            # Успешное обновление выручки
            messages.success(request, "Выручка успешно обновлена.")
        else:
            # Ошибка при обновлении выручки
            messages.error(request, "Ошибка обновления выручки.")

        return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))
