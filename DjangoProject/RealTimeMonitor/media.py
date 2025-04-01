import os.path

from django.utils import timezone
from bs4 import BeautifulSoup
import urllib.request
import requests
import re
from django.core.files import File
import uuid
from .models import MediaFile
import tempfile
import traceback

# Define headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def getSoup(url):
    # Fetches a webpage and returns a BeautifulSoup object
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    else:
        print(f"Failed to fetch {url}, Status Code: {response.status_code}")
        return None

def extractImageUrl(page_url):
    # Extracts the first image URL found in the page from a JavaScript variable
    soup = getSoup(page_url)
    if not soup:
        print(f"Failed to retrieve or parse {page_url}")
        return None

    script_tags = soup.find_all("script")
    for script in script_tags:
        if script.string:
            match = re.search(r'var\s+posterURL\s*=\s*"([^"]+)"', script.string)
            if match:
                full_url = match.group(1)
                print(f"Extracted Image URL from script: {full_url}")  # Debugging
                return full_url

    print(f"No image URL found on {page_url}")

def downloadImage(imageUrl, locationName):
    if not imageUrl:
        print("No image URL provided.")
        return None

    try:
        # Step 1: Download image to temp file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(urllib.request.urlopen(imageUrl).read())
            temp_file.flush()
            temp_file_path = temp_file.name

        # Step 2: Delete existing record (file + DB)
        existing_record = MediaFile.objects.filter(locationName=locationName).first()
        if existing_record:
            try:
                # Ensure any open file handle is closed.
                existing_record.mediaFile.close()
            except Exception as e:
                print(f"Error closing file handle for {locationName}: {e}")

            import time
            retries = 5
            deleted = False
            # Increase sleep interval to 1 second per attempt.
            for i in range(retries):
                try:
                    existing_record.mediaFile.delete(save=False)
                    deleted = True
                    break
                except PermissionError:
                    print(f"File locked for {locationName}, retrying deletion ({i+1}/{retries})...")
                    time.sleep(1)
            if not deleted:
                # If deletion still fails, log the issue and proceed.
                print(f"Unable to delete locked file for {locationName} after retries. " 
                      "Proceeding without file deletion. (This may leave orphan files.)")
            # Remove the DB record regardless.
            existing_record.delete()
            print(f"Deleted existing MediaFile record for {locationName}")

        # Step 3: Create and save a new record
        with open(temp_file_path, 'rb') as f:
            file_name = f"{uuid.uuid4()}.jpg"
            django_file = File(f, name=file_name)
            media_file = MediaFile(
                mediaFile=django_file,
                locationName=locationName,
                uploadedDate=timezone.now(),
                isManualUpload=False,
            )
            media_file.save()
            print(f"Saved new MediaFile with ID: {media_file.id}")
            return media_file

    except Exception as e:
        print(f"[DOWNLOAD ERROR] {imageUrl}: {e}")
        traceback.print_exc()
        return None

    finally:
        # Ensure the temp file is removed.
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except PermissionError:
                import time
                time.sleep(1)
                os.remove(temp_file_path)
