from orders.models import Order
from revenue.models import Revenue
import logging
from django.utils import timezone

logger = logging.getLogger(__name__)


class RevenueUpdater:
    """
    Класс для обновления данных о выручке за оплаченные заказы.
    """
    @staticmethod
    def filter_today_paid_orders():
        """
        Возвращает QuerySet оплаченных заказов за текущий день.
        """
        return Order.objects.filter(
            status=Order.PAID,
            created_at__date=timezone.now().date()
        )

    @classmethod
    def update_revenue(cls):
        """
        Обновляет данные о выручке за текущий день.

        Логика:
         - Если сегодня нет оплаченных заказов, возвращает None.
         - Если выручка успешно обновлена, возвращает True.
         - Если возникает ошибка, возвращает False.
        """
        logger.info("Starting revenue update...")

        try:
            orders = cls.filter_today_paid_orders()

            if not orders.exists():
                logger.info("No paid orders found for today.")
                return None

            # Подсчитываем общую сумму
            total_amount = sum(order.total_price or 0 for order in orders)

            today = timezone.now().date()

            # Ищем запись Revenue за сегодня (если несколько — возьмём последнюю)
            today_revenue_qs = Revenue.objects.filter(created_at__date=today)
            if today_revenue_qs.exists():
                today_revenue = today_revenue_qs.last()
                if today_revenue.amount != total_amount:
                    today_revenue.amount = total_amount
                    today_revenue.created_at = timezone.now()
                    today_revenue.save()
                    logger.info(f"Today's revenue updated to {total_amount}.")
                else:
                    # Сумма не изменилась, просто обновим время
                    today_revenue.created_at = timezone.now()
                    today_revenue.save()
                    logger.info(f"Revenue amount not changed ({total_amount}), timestamp updated.")
            else:
                # Сегодня ещё нет записи, создаём новую
                new_rev = Revenue.objects.create(amount=total_amount)
                logger.info(f"New revenue created: {new_rev.amount} (id={new_rev.id}).")

            logger.info("Revenue updated successfully.")
            return True

        except Exception as e:
            logger.error(f"Error during revenue update: {e}")
            return False
