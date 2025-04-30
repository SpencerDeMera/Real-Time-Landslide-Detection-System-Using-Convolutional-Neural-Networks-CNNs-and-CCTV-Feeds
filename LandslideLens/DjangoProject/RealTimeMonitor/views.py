from django.shortcuts import render, HttpResponse, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from .forms import UploadImageForm
from .models import MediaFile, feedSource, WeatherZone
from .cnn import loadModel, getTransform
from .media import extractImageUrl, downloadImage
from realtime.tasksQueue import tasksQueue
from .scraper import extractData, extractWeatherZones
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
    feedSources = feedSource.objects.all()
    weatherZones = WeatherZone.objects.all()
    return render(request, 'home.html', {
        'images': images,
        'weatherZones': feedSources,
        'weatherZones': weatherZones,
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
        'images': images,
        'feedSources': feedSources,
        'groupedFeedSources': groupedFeedSources,
    })

def getGroupedFeedSourcesJson(request):
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

    grouped = {}
    for key, group in groupby(feedSources, key=attrgetter('route')):
        grouped[key] = [
            {
                'id': fs.id,
                'streamSourceName': fs.streamSourceName,
                'county': fs.county,
                'nearbyPlace': fs.nearbyPlace,
                'lastPollDate': fs.lastPollDate.isoformat(),
                'isPolling': fs.isPolling
            } for fs in group
        ]

    return JsonResponse({'groupedFeedSources': grouped})

def getPollingFeedSourcesJson(request):
    feedSources = feedSource.objects.filter(
        isPolling=True
    ).order_by('-lastPollDate').values(
        'id',
        'streamSourceName',
        'county',
        'nearbyPlace',
        'lastPollDate',
        'isPolling',
        'route'
    )

    return JsonResponse({'feedSources': list(feedSources)})

def getPositivePredictedMediaFilesJson(request):
    mediaFiles = MediaFile.objects.filter(
        prediction=1
    ).order_by('-uploadedDate').values(
        'id',
        'mediaFile',
        'uploadedDate',
        'locationName',
        'prediction',
        'predictionString',
        'isManualUpload',
        'feed_id'
    )

    return JsonResponse({'mediaFiles': list(mediaFiles)})

def checkIfZoneIsValidForCountyJson(zoneCodes):
    return WeatherZone.objects.filter(
        zoneCode__in=zoneCodes,
        county__in=feedSource.objects.values('county')
    ).exists()


@csrf_exempt
def checkIfZoneIsValidForCountyJson(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            zoneCodes = data.get('zoneCodes', [])

            if not zoneCodes:
                return JsonResponse({'error': 'No zone codes provided'}, status=400)

            is_valid = WeatherZone.objects.filter(
                zoneCode__in=zoneCodes,  # Note: underscore
                county__in=feedSource.objects.values('county')
            ).exists()

            return JsonResponse({'isValid': is_valid})

        except json.JSONDecodeError as e:
            return JsonResponse({'error': f'Invalid JSON: {str(e)}'}, status=400)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    return JsonResponse({'error': 'Only POST requests allowed'}, status=400)

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
    errors = []

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

            max = hours * 4  # Since it's every 30 mins

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
                        image_result = extractImageUrl(feed.streamSource)
                        if not image_result["success"]:
                            errors.append(f"{feed.streamSourceName}: {image_result['error']}")
                            continue

                        feedSourceImageURL = image_result["image_url"]

                        result = downloadImage(feedSourceImageURL, feed.streamSourceName)
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
                tasksQueue.put((feedSourceIds, max))

            if errors:
                # Return errors as JSON
                return JsonResponse({
                    'success': False,
                    'errors': errors,
                }, status=400)  # HTTP 400 for client errors
            else:
                # Return success response
                return JsonResponse({
                    'success': True,
                    'redirect_url': '/analyze/',  # Optional: Redirect on success
                })

        except ValueError as e:
            return JsonResponse({
                'success': False,
                'error': 'Invalid ID format',
            }, status=400)

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Server error: {str(e)}',
            }, status=500)  # HTTP 500 for server errors

    return JsonResponse({
        'success': False,
        'error': 'Invalid request method',
    }, status=405)  # HTTP 405 for wrong method

def scrapeAndSaveFeedData(request):
    if request.method == "POST":
        MASTER_PAGE_URL = "https://cwwp2.dot.ca.gov/vm/streamlist.htm"
        data = extractData(MASTER_PAGE_URL)

        created_count = 0
        for item in data:
            # Check if a record with these exact fields already exists
            obj, created = feedSource.objects.get_or_create(
                streamSource=item["streamSource"],
                streamSourceName=item["streamSourceName"],
                route=item["route"],
                county=item["county"],
                nearbyPlace=item["nearbyPlace"],
                defaults={
                    'isPolling': False
                }
            )
            if created:
                created_count += 1

        messages.success(request, f"Data scraped successfully! {created_count} new records added.")
        return redirect("home")

    return render(request, 'home.html')

def scrapeNWSZoneData(request):
    if request.method == "POST":
        url = "https://www.weather.gov/source/gis/Shapefiles/County/bp05mr24.dbx"
        zoneData = extractWeatherZones(url)

        created_count = 0
        for zone in zoneData:
            # Check if a record with this zoneId already exists
            obj, created = WeatherZone.objects.get_or_create(
                zoneId=zone["zoneId"],
                defaults={
                    'state': zone["state"],
                    'region': zone["region"],
                    'zoneName': zone["zoneName"],
                    'zoneCode': zone["zoneCode"],
                    'county': zone["county"],
                    'fipsCode': zone["fipsCode"],
                    'zoneType': zone["zoneType"],
                    'direction': zone["direction"],
                    'latitude': zone["latitude"],
                    'longitude': zone["longitude"],
                }
            )
            if created:
                created_count += 1

        messages.success(request, f"Data scraped successfully! {created_count} new records added.")
        return redirect("home")

    return render(request, 'home.html')

def bulkFeedSourceDelete(request):
    if request.method == 'POST':
        # Get the list of selected image IDs
        selectedIds = request.POST.getlist('selectedIds')

        # Delete the selected images
        feedSource.objects.filter(id__in=selectedIds).delete()

        return redirect('images')  # Redirect to the image table page after deletion
    else:
        return HttpResponse("Invalid request method", status=400)