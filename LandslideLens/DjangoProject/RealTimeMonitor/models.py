from django.db import models
from django.db.models.signals import post_delete
from django.dispatch import receiver
import uuid
import os
import gc

# python manage.py makemigrations
# python manage.py migrate

class MediaFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    mediaFile = models.ImageField(upload_to='uploads/')
    uploadedDate = models.DateTimeField(auto_now_add=True)
    locationName = models.CharField(max_length=255, null=True, blank=True)
    prediction = models.IntegerField(null=True, blank=True)
    predictionString = models.CharField(max_length=255, null=True, blank=True)
    isManualUpload = models.BooleanField(default=False, null=True)
    feed = models.ForeignKey("feedSource", on_delete=models.CASCADE, null=True, blank=True, related_name="mediaFiles")

class feedSource(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    streamSource = models.CharField(max_length=255, null=True, blank=True)
    streamSourceName = models.CharField(max_length=255, null=True, blank=True)
    route = models.CharField(max_length=255, null=True, blank=True)
    county = models.CharField(max_length=255, null=True, blank=True)
    nearbyPlace = models.CharField(max_length=255, null=True, blank=True)
    isPolling = models.BooleanField(default=False, blank=True)
    lastPollDate = models.DateTimeField(auto_now=True, blank=True)

class WeatherZone(models.Model):
    state = models.CharField(max_length=2)
    zoneId = models.CharField(max_length=10)
    region = models.CharField(max_length=10)
    zoneName = models.CharField(max_length=100)
    zoneCode = models.CharField(max_length=10, unique=True)
    county = models.CharField(max_length=100)
    fipsCode = models.CharField(max_length=10)
    zoneType = models.CharField(max_length=1)
    direction = models.CharField(max_length=10)
    latitude = models.FloatField()
    longitude = models.FloatField()

@receiver(post_delete, sender=MediaFile)
def auto_delete_file_on_delete(sender, instance, **kwargs):
    if instance.mediaFile:
        try:
            # Force-close the file handle if it's open
            instance.mediaFile.close()
        except Exception as e:
            print(f"Error closing file handle for {instance.mediaFile.path}: {e}")
        # Run garbage collection to help release any locks
        gc.collect()
        try:
            os.remove(instance.mediaFile.path)
        except Exception as e:
            print(f"Error deleting file {instance.mediaFile.path}: {e}")

