from django.apps import AppConfig

class RealTimeMonitorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'RealTimeMonitor'

    def ready(self):
        from realtime.tasksQueue import runCleanupScheduler, startQueueWorker
        runCleanupScheduler()
        startQueueWorker()
