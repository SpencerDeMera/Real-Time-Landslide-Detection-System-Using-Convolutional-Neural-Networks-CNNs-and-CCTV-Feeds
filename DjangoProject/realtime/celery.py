from __future__ import absolute_import
import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'realtime.settings')
app = Celery('realtime')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

CELERY_BEAT_SCHEDULE = {
    'cleanupOldImagesDaily': {
        'task': 'realtime.cleanupOldImages',
        'schedule': crontab(hour=0, minute=0),  # every day at midnight
    },
}
