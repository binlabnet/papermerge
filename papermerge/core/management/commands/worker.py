import logging

from celery import Celery
from celery.apps.worker import Worker as CeleryWorker
from django.core.management.base import BaseCommand
from papermerge.core.models import Document

logger = logging.getLogger(__name__)
celery_app = Celery('papermerge')


@celery_app.task
def txt2db():
    """
    Move OCRed text from txt files into database
    """
    logger.debug("Celery beat: txt2db")

    for doc in Document.objects.all():
        doc.update_text_field()


@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Calls every 30 seconds txt2db
    sender.add_periodic_task(
        30.0, txt2db.s(), name='txt2db'
    )


class Command(BaseCommand):

    help = """Async Celery Worker"""

    def add_arguments(self, parser):
        pass

    def handle(self, *args, **options):
        celery_app.config_from_object(
            'django.conf:settings', namespace='CELERY'
        )

        # Load task modules from all registered Django app configs.
        celery_app.autodiscover_tasks()

        celery_worker = CeleryWorker(
            hostname="localhost",
            app=celery_app,
            beat=True
        )
        celery_worker.start()
