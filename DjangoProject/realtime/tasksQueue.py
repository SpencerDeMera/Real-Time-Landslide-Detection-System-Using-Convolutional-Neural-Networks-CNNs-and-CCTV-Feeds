from queue import Queue
import threading
import time
from datetime import datetime, timedelta

# Global queue for scheduled tasks
tasksQueue = Queue()

def queueWorker():
    while True:
        # Block until an item is available
        feedSourceIds, maxNumRuns = tasksQueue.get()
        for i in range(1, maxNumRuns + 1):
            print(f"[Queue] Running analyzeImagesTask for feeds {feedSourceIds}, iteration {i}/{maxNumRuns}")
            try:
                # Import here to avoid circular imports
                from RealTimeMonitor.backgroundTasks import analyzeImagesTask
                analyzeImagesTask(feedSourceIds, i, maxNumRuns)
            except Exception as e:
                print(f"Exception in analyzeImagesTask: {e}")
            if i < maxNumRuns:
                time.sleep(900)  # 15 minutes
        tasksQueue.task_done()

def startQueueWorker():
    t = threading.Thread(target=queueWorker, daemon=True)
    t.start()

def runCleanupScheduler():
    def scheduler():
        from RealTimeMonitor.backgroundTasks import cleanupOldImages  # Import here to avoid circular import

        # Run once on startup
        try:
            print("[Cleanup] Running initial cleanupOldImages()")
            cleanupOldImages()
        except Exception as e:
            print(f"[Cleanup] Initial cleanup failed: {e}")

        while True:
            # Calculate seconds until next midnight
            now = datetime.now()
            nextMidnight = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            secondsToMidnight = (nextMidnight - now).total_seconds()
            print(f"[Cleanup] Sleeping {secondsToMidnight:.1f} seconds until midnight")

            time.sleep(secondsToMidnight)

            try:
                print("[Cleanup] Running scheduled cleanupOldImages()")
                cleanupOldImages()
            except Exception as e:
                print(f"[Cleanup] Scheduled cleanup failed: {e}")

    t = threading.Thread(target=scheduler, daemon=True)
    t.start()

