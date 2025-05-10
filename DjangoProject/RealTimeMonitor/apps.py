from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'RealTimeMonitor'
    def ready(self):
        from realtime.tasksQueue import runCleanupScheduler, startQueueWorker
        runCleanupScheduler()
        startQueueWorker()
