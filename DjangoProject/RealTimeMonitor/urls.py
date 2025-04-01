from django.urls import path
from .views import home, analyze, images, tasks, about, imageUpload, imageDelete, bulkImageDelete, analyzeImage, bulkAnalyzeImages, scrapeAndSaveFeedData, bulkFeedSourceDelete
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', home, name='home'),
    path('analyze/', analyze, name="analyze"),
    path('images/', images, name="images"),
    path('tasks/', tasks, name="tasks"),
    path('about/', about, name="about"),
    path('imageUpload/', imageUpload, name='imageUpload'),
    path('imageDelete/<uuid:image_id>/', imageDelete, name='imageDelete'),
    path('bulkImageDelete/', bulkImageDelete, name='bulkImageDelete'),
    path('analyzeImage/<uuid:image_id>/', analyzeImage, name='analyzeImage'),
    path('bulkAnalyzeImages/', bulkAnalyzeImages, name='bulkAnalyzeImages'),
    path('scrapeAndSaveFeedData/', scrapeAndSaveFeedData, name='scrapeAndSaveFeedData'),
    path('bulkFeedSourceDelete/', bulkFeedSourceDelete, name='bulkFeedSourceDelete'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)