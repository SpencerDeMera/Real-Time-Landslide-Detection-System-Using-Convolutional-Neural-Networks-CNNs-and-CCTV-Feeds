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
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

# Define headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def getSoup(url):
    # Fetches a webpage and returns a BeautifulSoup object
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        if response.status_code == 200:
            return {
                "success": True,
                "soup": BeautifulSoup(response.text, "html.parser"),
                "error": None
            }
        else:
            return {
                "success": False,
                "soup": None,
                "error": f"Failed to fetch {url}, status code: {response.status_code}"
            }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "soup": None,
            "error": f"Network error while requesting {url}"
        }


def extractImageUrl(pageURL):
    result = getSoup(pageURL)

    if not result["success"]:
        error_msg = result["error"]

        # Optional: parse for known patterns like timeouts
        if "timed out" in error_msg.lower():
            return {
                "success": False,
                "image_url": None,
                "error": f"URL source capture for {pageURL} timed out — check your internet connection."
            }
        elif "Failed to establish a new connection" in error_msg or "Name or service not known" in error_msg:
            return {
                "success": False,
                "image_url": None,
                "error": f"Network error while accessing the image URL {pageURL} — check DNS or connectivity."
            }
        else:
            return {
                "success": False,
                "image_url": None,
                "error": error_msg
            }

    soup = result["soup"]
    script_tags = soup.find_all("script")

    for script in script_tags:
        if script.string:
            match = re.search(r'var\s+posterURL\s*=\s*"([^"]+)"', script.string)
            if match:
                full_url = match.group(1)
                print(f"Extracted Image URL from script: {full_url}")
                return {
                    "success": True,
                    "image_url": full_url,
                    "error": None
                }

    error_msg = f"No image URL found in scripts on {pageURL}"
    print(error_msg)
    return {
        "success": False,
        "image_url": None,
        "error": error_msg
    }

def downloadImage(imageUrl, locationName):
    result = {
        "success": False,
        "mediaFileToAddorUpdate": None,
        "error": None,
    }

    tempFile_path = None

    if not imageUrl:
        result["error"] = "No image URL provided."
        return result

    try:
        # Step 1: Download image to temp file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tempFile:
            try:
                response = urllib.request.urlopen(imageUrl, timeout=10)
                tempFile.write(response.read())
                tempFile.flush()
                tempFile_path = tempFile.name
            except urllib.error.URLError as e:
                if isinstance(e.reason, TimeoutError):
                    result["error"] = f"Image download for {locationName} timed out — check your internet connection."
                else:
                    result["error"] = f"Network error while accessing the image for {locationName} at URL: {imageUrl}"
                return result
            except Exception as e:
                result["error"] = f"Unexpected error during download: {str(e)}"
                return result

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
                print(f"Unable to delete locked file for {locationName} after retries. Proceeding without file deletion. (This may leave orphan files.)")
            # Remove the DB record regardless.
            existing_record.delete()
            print(f"Deleted existing MediaFile record for {locationName}")

        # Step 3: Create and save a new record
        with open(tempFile_path, 'rb') as f:
            file_data = f.read()
            fileName = f"{uuid.uuid4()}.jpg"
            saved_path = default_storage.save(f"uploads/{fileName}", ContentFile(file_data))

            mediaFileToAddorUpdate = MediaFile(
                mediaFile=saved_path,  # <-- This is just the relative path (string)
                locationName=locationName,
                uploadedDate=timezone.now(),
                isManualUpload=False,
            )
            mediaFileToAddorUpdate.save()
            
            print(f"Saved new MediaFile with ID: {mediaFileToAddorUpdate.id}")
            
            result["success"] = True
            result["mediaFileToAddorUpdate"] = {
                "id": str(mediaFileToAddorUpdate.id),
                "file_url": mediaFileToAddorUpdate.mediaFile.url,
                "location_name": mediaFileToAddorUpdate.locationName
            }
            return result

    except Exception as e:
        result["error"] = f"Unexpected processing error: {e}"
        traceback.print_exc()
        return result

    finally:
        # Ensure the temp file is removed.
        if 'tempFile_path' in locals() and os.path.exists(tempFile_path):
            try:
                os.remove(tempFile_path)
            except PermissionError:
                import time
                time.sleep(1)
                os.remove(tempFile_path)
