from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .forms import UploadImageForm
from .models import TaskItem, MediaFile, feedSource
from .cnn import loadModel, getTransform
from .media import extractImageUrl, downloadImage
from .backgroundTasks import analyzeImagesTask
from .scraper import extractData
from django.utils.safestring import mark_safe
from django.db.models import Case, When, Value, IntegerField
from django.db.models.functions import Substr, Cast
from PIL import Image
from uuid import UUID
from django.utils import timezone
from itertools import groupby
from operator import attrgetter
import torch
import torch.nn.functional as F
import io
import json

def home(request):
    images = MediaFile.objects.all().order_by('-uploadedDate')
    return render(request, 'home.html', {
        'images': images,  # Pass the images to the template
    })

def analyze(request):
    image_form = UploadImageForm()
    images = MediaFile.objects.all().order_by('-uploadedDate')[:1]

    feedSources = feedSource.objects.annotate(
        routeOrder=Case(
            When(route__startswith='I-', then=Value(1)),
            When(route__startswith='US-', then=Value(2)),
            When(route__startswith='SR-', then=Value(3)),
            default=Value(4),
            output_field=IntegerField()
        ),
        routeNum=Case(
            When(route__startswith='I-', then=Cast(Substr('route', 3), output_field=IntegerField())),
            When(route__startswith='US-', then=Cast(Substr('route', 4), output_field=IntegerField())),
            When(route__startswith='SR-', then=Cast(Substr('route', 4), output_field=IntegerField())),
            default=Value(4),
            output_field=IntegerField()
        )
    ).order_by('routeOrder', 'routeNum')

    groupedFeedSources = {}
    for key, group in groupby(feedSources, key=attrgetter('route')):
        groupedFeedSources[key] = list(group)

    return render(request, 'analyze.html', {
        'image_form': image_form,
        'images': images,  # Pass the images to the template
        'feedSources': feedSources,
        'groupedFeedSources': groupedFeedSources,
    })

def images(request):
    # Get sorting and filtering parameters from GET request
    sort_order = request.GET.get('sort', '-uploadedDate')  # Default sort by uploadedDate
    filter_prediction = request.GET.get('filter', 'all')  # Default show all
    search_query = request.GET.get('search', '')

    # Query media files
    mediaFiles = MediaFile.objects.all()

    # Apply filtering based on prediction
    if filter_prediction == "landslide":
        mediaFiles = mediaFiles.filter(prediction=1)
    elif filter_prediction == "normal":
        mediaFiles = mediaFiles.filter(prediction=0)

    if search_query:
        mediaFiles = mediaFiles.filter(locationName__icontains=search_query)

    # Apply sorting
    if sort_order in ["-uploadedDate", "uploadedDate", "locationName", "-locationName", "prediction", "-prediction"]:
        mediaFiles = mediaFiles.order_by(sort_order)

    return render(request, 'imageTable.html', {'mediaFiles': mediaFiles, 'filter_prediction': filter_prediction, 'sort_order': sort_order})


def tasks(request):
    items = TaskItem.objects.all()
    return render(request, 'tasks.html', {'tasks': items})

def about(request):
    return render(request, 'about.html')

def imageUpload(request):
    if request.method == 'POST':
        form = UploadImageForm(request.POST, request.FILES)
        if form.is_valid():
            # Save the uploaded image to the database
            mediaFile = MediaFile(
                mediaFile=request.FILES['image'],
                locationName=form.cleaned_data['locationName']  # Save location name
            )
            mediaFile.save()
            return redirect('analyze')  # Redirect back to the home page after upload
    else:
        form = UploadImageForm()

    return render(request, 'analyze.html', {'image_form': form})

def imageDelete(request, image_id):
    # Get the image object or return a 404 error if it doesn't exist
    image = get_object_or_404(MediaFile, id=image_id)

    # Delete the image file from the file system
    image.mediaFile.delete()
    image.delete()

    return redirect('analyze')

def bulkImageDelete(request):
    if request.method == 'POST':
        # Get the list of selected image IDs
        selectedIds = request.POST.getlist('selectedIds')

        # Delete the selected images
        MediaFile.objects.filter(id__in=selectedIds).delete()

        return redirect('images')  # Redirect to the image table page after deletion
    else:
        return HttpResponse("Invalid request method", status=400)

@csrf_exempt  # Disable CSRF protection for this view (use with caution)
def analyzeImage(request, image_id):
    # Load the model and transform
    model = loadModel()
    transform = getTransform()

    if request.method == 'POST':
        try:
            # Read the image file from the request
            imageFile = request.FILES['file']
            imageBytes = imageFile.read()
            image = Image.open(io.BytesIO(imageBytes)).convert("RGB")  # Convert to RGB

            # Apply transformations
            image = transform(image).unsqueeze(0)  # Add batch dimension

            # Make prediction
            with torch.no_grad():
                output = model(image)
                probabilities = F.softmax(output, dim=1)
                prediction = torch.argmax(probabilities, dim=1).item()

            # Map prediction to a string
            predictionStr = mark_safe('Landslide/Road Anomaly') if prediction == 1 else mark_safe('Normal Conditions')

            # Save the prediction to the corresponding MediaFile object
            mediaFile = get_object_or_404(MediaFile, id=image_id)
            mediaFile.prediction = prediction
            mediaFile.predictionString = predictionStr
            mediaFile.save()

            # Return the prediction result as a JSON object
            return JsonResponse({'result': predictionStr})
        except Exception as e:
            # Log the error and return a meaningful error message
            print(f"Error analyzing image: {e}")
            return JsonResponse({'error': str(e)}, status=500)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)


@csrf_exempt
def bulkAnalyzeImages(request):
    if request.method == "POST":
        try:
            # Handle both form data and JSON input
            if request.content_type == 'application/json':
                data = json.loads(request.body)
                selectedIds = data.get('selectedIds', [])
                hours = int(data.get('hours', 1))  # Default to 1 hour
            else:
                selectedIds = request.POST.getlist('selectedIds')
                hours = int(request.POST.get('analysisDuration', 1))

            max = hours * 5  # Since it's every 30 mins

            # Convert to UUIDs
            feedSourceIds = [UUID(id) for id in selectedIds]
            selectedFeeds = feedSource.objects.filter(id__in=feedSourceIds)

            if (max == 0):
                model = loadModel()
                transform = getTransform()

                mediaFileIds = []
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
                        image = Image.open(io.BytesIO(imageBytes)).convert("RGB")
                        image = transform(image).unsqueeze(0)

                        with torch.no_grad():
                            output = model(image)
                            probabilities = F.softmax(output, dim=1)
                            prediction = torch.argmax(probabilities, dim=1).item()

                        predictionStr = 'Landslide/Road Anomaly' if prediction == 1 else 'Normal Conditions'
                        mediaFile.prediction = prediction
                        mediaFile.predictionString = predictionStr
                        if mediaFile.feed:
                            mediaFile.feed.isPolling = False
                            mediaFile.feed.save()
                        mediaFile.save()

                        print(f"Analyzed image {mediaFile.id} - Prediction: {predictionStr}")
                    except Exception as e:
                        print(f"Error analyzing media {mediaFileId}: {e}")
                        continue
            else:
                analyzeImagesTask.delay(feedSourceIds, i=1, max=max)

            return redirect("analyze")

        except ValueError as e:
            error_msg = 'Invalid ID format'
            return render(request, 'analyze.html', {'error': error_msg})

        except Exception as e:
            error_msg = f'Server error: {str(e)}'
            return render(request, 'analyze.html', {'error': error_msg})

    return render(request, 'analyze.html')

def scrapeAndSaveFeedData(request):
    if request.method == "POST":
        MASTER_PAGE_URL = "https://cwwp2.dot.ca.gov/vm/streamlist.htm"
        data = extractData(MASTER_PAGE_URL)

        for item in data:
            feedSource.objects.create(
                streamSource=item["streamSource"],
                streamSourceName=item["streamSourceName"],
                route=item["route"],
                county=item["county"],
                nearbyPlace=item["nearbyPlace"],
                isPolling=False
            )

        messages.success(request, "Data scraped and saved successfully!")
        return redirect("analyze")

    return render(request, 'analyze.html')

def bulkFeedSourceDelete(request):
    if request.method == 'POST':
        # Get the list of selected image IDs
        selectedIds = request.POST.getlist('selectedIds')

        # Delete the selected images
        feedSource.objects.filter(id__in=selectedIds).delete()

        return redirect('images')  # Redirect to the image table page after deletion
    else:
        return HttpResponse("Invalid request method", status=400)