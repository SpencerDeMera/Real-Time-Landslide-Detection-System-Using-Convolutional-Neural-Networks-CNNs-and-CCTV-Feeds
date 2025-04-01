from celery import shared_task
from RealTimeMonitor.models import MediaFile, feedSource
from .cnn import loadModel, getTransform
from .media import extractImageUrl, downloadImage
from PIL import Image
from datetime import timedelta
from django.utils import timezone
import torch
import torch.nn.functional as F
import io

@shared_task
def analyzeImagesTask(feedSourceIds, i, max):
    try:
        model = loadModel()
        transform = getTransform()

        mediaFileIds = []
        selectedFeeds = feedSource.objects.filter(id__in=feedSourceIds)
        for feed in selectedFeeds:
            try:
                print(f"Processing feed: {feed.streamSourceName}")
                feedSourceImageURL = extractImageUrl(feed.streamSource)

                mediaFile = downloadImage(feedSourceImageURL, feed.streamSourceName)

                feed.isPolling = True
                feed.lastPollDate = timezone.now()
                feed.save()

                mediaFile.feed = feed
                mediaFile.save()

                mediaFileIds.append(str(mediaFile.id))

            except Exception as e:
                print(f"Error analyzing image from {feed.streamSourceName}: {e}")
                continue

        for mediaFileId in mediaFileIds:
            try:
                mediaFile = MediaFile.objects.get(id=mediaFileId)
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
        # Schedule next run if needed
        elif i < max:
            analyzeImagesTask.apply_async(args=[feedSourceIds, i + 1, max], countdown=10 * 60)
    except Exception as e:
        print(f"[TASK ROOT ERROR] {e}")
        raise


@shared_task
def cleanupOldImages():
    cuttOff = timezone.now() - timedelta(days=14)
    # Filter for images older than 14 days with prediction equal to 0
    oldMediaFiles = MediaFile.objects.filter(uploadedDate__lt=cuttOff, prediction=0)
    count = oldMediaFiles.count()
    oldMediaFiles.delete()
    print(f"Deleted {count} old images with prediction 0")