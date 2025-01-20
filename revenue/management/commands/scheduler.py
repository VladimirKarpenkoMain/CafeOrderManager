import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from django.conf import settings
from django.core.management import BaseCommand
from django_apscheduler import util
from django_apscheduler.jobstores import DjangoJobStore
from django_apscheduler.models import DjangoJobExecution

from revenue.tasks import RevenueUpdater

logger = logging.getLogger(__name__)


@util.close_old_connections
def delete_old_job_executions(max_age=settings.DELETE_OLD_JOB_MAX_AGE):
    """
    Удаляет записи о выполненных задачах, старше max_age секунд.
    """
    DjangoJobExecution.objects.delete_old_job_executions(max_age)


class Command(BaseCommand):
    """
    Команда для запуска планировщика задач (scheduler) с использованием APScheduler.
    """
    help = "Запускает Scheduler для периодического выполнения задач."

    def handle(self, *args, **options):
        """
        Основной метод для запуска планировщика задач.
        """
        # Инициализация планировщика с использованием часового пояса из настроек
        scheduler = BlockingScheduler(timezone=settings.TIME_ZONE)
        scheduler.add_jobstore(DjangoJobStore(), "default")

        # Добавление задачи для обновления выручки
        scheduler.add_job(
            RevenueUpdater.update_revenue,
            trigger=CronTrigger(hour=settings.UPDATE_REVENUE_TASK, minute=0),
            id="update_revenue",
            max_instances=1,  # Ограничение количества одновременных запусков
            replace_existing=True,  # Замена задачи, если идентификатор совпадает
        )
        logger.info("Добавлена задача 'update_revenue'.")

        # Добавление задачи для удаления старых записей о выполненных задачах
        scheduler.add_job(
            delete_old_job_executions,
            trigger=CronTrigger(day_of_week="mon", hour="00", minute="00"),  # Выполнение каждый понедельник в 00:00
            id="delete_old_job_executions",
            max_instances=1,
            replace_existing=True,
        )
        logger.info("Задача 'delete_old_job_executions' успешно добавлена!")

        try:
            logger.info("Scheduler успешно запущен!")
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Остановка scheduler...")
            scheduler.shutdown()
            logger.info("Scheduler успешно остановлен!")
