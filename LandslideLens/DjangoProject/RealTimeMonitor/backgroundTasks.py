from RealTimeMonitor.models import MediaFile, feedSource
from .cnn import loadModel, getTransform
from .media import extractImageUrl, downloadImage
from PIL import Image
from datetime import timedelta
from django.utils import timezone
from django.db import close_old_connections
import torch
import torch.nn.functional as F
import io
import os
import time

def waitForMediaFile(filePath, timeout=5.0, pollInterval=0.05):
    start = time.time()
    while time.time() - start < timeout:
        if filePath and os.path.exists(filePath):
            return True
        time.sleep(pollInterval)
    return False

def analyzeImagesTask(feedSourceIds, i, max):
    close_old_connections()
    errors = []

    try:
        model = loadModel()
        transform = getTransform()

        mediaFileIds = []
        selectedFeeds = feedSource.objects.filter(id__in=feedSourceIds)
        
        for feed in selectedFeeds:
            try:
                print(f"Processing feed: {feed.streamSourceName}")
                feedSourceImageURL = extractImageUrl(feed.streamSource)

                result = downloadImage(feedSourceImageURL["image_url"], feed.streamSourceName)

                if not result["success"]:
                    errors.append(f"{feed.streamSourceName}: {result['error']}")
                    continue

                mediaFile = MediaFile.objects.get(id=result["mediaFileToAddorUpdate"]["id"])
                feed.isPolling = True
                feed.lastPollDate = timezone.now()
                feed.save()

                mediaFile.feed = feed
                mediaFile.save()

                mediaFileIds.append(str(result["mediaFileToAddorUpdate"]["id"]))

            except Exception as e:
                print(f"Error analyzing image from {feed.streamSourceName}: {e}")
                continue

        for mediaFileId in mediaFileIds:
            try:
                mediaFile = MediaFile.objects.get(id=mediaFileId)
                file_path = getattr(mediaFile.mediaFile, 'path', None)
                print(f"Waiting for file: {file_path}")
                if not waitForMediaFile(file_path):
                    print(f"File did not appear in time for mediaFileId {mediaFileId}. Skipping.")
                    continue

                print(f"Opening file: {file_path}")
                imageBytes = mediaFile.mediaFile.read()
                mediaFile.mediaFile.close()
                image = Image.open(io.BytesIO(imageBytes)).convert("RGB")
                image = transform(image).unsqueeze(0)

                with torch.no_grad():
                    output = model(image)
                    probabilities = F.softmax(output, dim=1)
                    prediction = torch.argmax(probabilities, dim=1).item()

                predictionStr = 'Landslide/Road Anomaly' if prediction == 1 else 'Normal Conditions'
                mediaFile.prediction = prediction
                mediaFile.predictionString = predictionStr
                mediaFile.save()

                print(f"[Iter {i}] Analyzed image {mediaFile.id} - Prediction: {predictionStr}")
            except Exception as e:
                print(f"Error analyzing media {mediaFileId}: {e}")
                continue

        # Final run - update polling status of feedSource
        if i >= max:
            for feedSourceId in feedSourceIds:
                try:
                    feed = feedSource.objects.get(id=feedSourceId)
                    if feed:
                        feed.isPolling = False
                        feed.save()
                except Exception as e:
                    print(f"Error marking feed polling complete: {e}")
    except Exception as e:
        print(f"[TASK ROOT ERROR] {e}")

def cleanupOldImages():
    cuttOff = timezone.now() - timedelta(days=14)
    # Filter for images older than 14 days with prediction equal to 0
    oldMediaFiles = MediaFile.objects.filter(uploadedDate__lt=cuttOff, prediction=0)
    count = oldMediaFiles.count()
    oldMediaFiles.delete()
    print(f"Deleted {count} old images with prediction 0")