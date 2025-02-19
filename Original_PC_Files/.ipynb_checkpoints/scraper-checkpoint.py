import os
import requests
import re
import random
import time
import pytesseract
import imagehash 
import uuid
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import urllib.request
from PIL import Image, ImageEnhance

DEBUG = True

# Define the master webpage URL
MASTER_PAGE_URL = "https://cwwp2.dot.ca.gov/vm/streamlist.htm"  # Replace with the actual master page URL

# Define headers to mimic a real browser
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

# Directories for saving images
BASE_DIR = "/mnt/c/Users/spenc/Desktop/CpE-Projects/GradProject/RAW_CCTV_Images"
TRAINING_DIR = os.path.join(BASE_DIR, "training")
TESTING_DIR = os.path.join(BASE_DIR, "testing")

# Store known "error image" hashes to compare against
KNOWN_ERROR_HASHES = set()

def get_soup(url):
    # Fetches a webpage and returns a BeautifulSoup object
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return BeautifulSoup(response.text, "html.parser")
    else:
        print(f"Failed to fetch {url}, Status Code: {response.status_code}")
        return None

def extract_links(master_url):
    # Extracts all valid hyperlinks from the master page
    soup = get_soup(master_url)
    if not soup:
        return []

    links = []
    for a_tag in soup.find_all("a", href=True):
        full_link = urljoin(master_url, a_tag["href"])  # Ensure absolute URL
        links.append(full_link)
    
    return links

def extract_image_url(page_url):
    # Extracts the first image URL found in the page from a JavaScript variable
    soup = get_soup(page_url)
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
    return None

def assign_directory():
    # Assigns an image to either training (80%) or testing (20%) independently
    return TRAINING_DIR
    # return TRAINING_DIR if random.random() < 0.8 else TESTING_DIR

def is_error_image(image_path):
    # Detects if an image is an error page by checking OCR in both normal and flipped orientations
    try:
        image = Image.open(image_path)

        # 1️⃣ **Check OCR on the original image**
        text_original = pytesseract.image_to_string(image).strip()
        
        # 2️⃣ **Check OCR on the flipped version**
        flipped_image = image.transpose(Image.FLIP_LEFT_RIGHT)
        text_flipped = pytesseract.image_to_string(flipped_image).strip()

        # 3️⃣ **Detect error message in either version**
        if "Temporarily Unavailable" in text_original or "Temporarily Unavailable" in text_flipped:
            print(f"❌ Discarding error image (Detected in OCR): {image_path}")
            return True

        # 4️⃣ **Check for duplicate patterns using perceptual hashing**
        image_hash = imagehash.average_hash(image)
        if image_hash in KNOWN_ERROR_HASHES:
            print(f"❌ Discarding error image (Hash match): {image_path}")
            return True
        else:
            KNOWN_ERROR_HASHES.add(image_hash)  # Store hash if it's a new image

        return False  # Valid image

    except Exception as e:
        print(f"Error checking image {image_path}: {e}")
        return False  # Assume valid if an error occurs

def save_image(image_path, image):
    # Saves an image to the specified path
    try:
        image.save(image_path)
        print(f"Saved: {image_path}")
    except Exception as e:
        print(f"Error saving {image_path}: {e}")

def process_image(image_path):
    # Loads an image, filters error images, and saves multiple variations
    try:
        image = Image.open(image_path)

        # Check if it's an error image
        if is_error_image(image_path):
            os.remove(image_path)  # Delete the bad image
            return  # Skip processing

        # Assign directories independently for each variation
        original_dir = assign_directory()
        flipped_dir = assign_directory()
        rotated_dir = assign_directory()
        darkened_dir = assign_directory()
        brightened_dir = assign_directory()

        # Generate base filename using GUID
        base_name = os.path.basename(image_path)
        flipped_name = f"flipped_{base_name}"
        rotated_name = f"rotated_{base_name}"
        darkened_name = f"darkened_{base_name}"
        brightened_name = f"brightened_{base_name}"
        
        # Paths for saving variations
        original_save_path = os.path.join(original_dir, base_name)
        flipped_save_path = os.path.join(flipped_dir, flipped_name)
        rotated_save_path = os.path.join(rotated_dir, rotated_name)
        darkened_save_path = os.path.join(darkened_dir, darkened_name)
        brightened_save_path = os.path.join(brightened_dir, brightened_name)

        # Save the original image
        save_image(original_save_path, image)

        # Create and save flipped image
        flipped_image = image.transpose(Image.FLIP_LEFT_RIGHT)
        save_image(flipped_save_path, flipped_image)

        # Create and save rotated 180-degree image
        rotated_image = image.rotate(180)
        save_image(rotated_save_path, rotated_image)

        # Create and save darkened image
        enhancer = ImageEnhance.Brightness(image)
        darkened_image = enhancer.enhance(0.5)  # Reduce brightness by 50%
        save_image(darkened_save_path, darkened_image)

        # Create and save brightened image
        brightened_image = enhancer.enhance(1.5)  # Increase brightness by 50%
        save_image(brightened_save_path, brightened_image)

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

def download_image(image_url):
    # Downloads an image, filters error images, saves it, and processes it
    if not image_url:
        print("No image URL provided.")
        return

    # Generate a unique filename using GUID
    unique_filename = f"{uuid.uuid4()}.jpg"

    temp_path = os.path.join(BASE_DIR, unique_filename)  # Temporary storage

    try:
        urllib.request.urlretrieve(image_url, temp_path)
        print(f"Downloaded: {temp_path}")

        # Process the image (check if error, flip & move to appropriate directory)
        process_image(temp_path)

        # Remove temp file
        os.remove(temp_path)

    except Exception as e:
        print(f"Error downloading {image_url}: {e}")

def main():
    # Runs the image extraction and downloading process three times, 
    # with a 5-minute wait between each cycle
    # Step 1: Extract links once (so we use the same links for all 3 cycles)
    links = extract_links(MASTER_PAGE_URL)
    if not links:
        print("No links found. Exiting process.")
        return
    
    print(f"Found {len(links)} links. Starting download process.")

    for cycle in range(3):  # Repeat process 3 times
        print(f"\n--- Cycle {cycle + 1}/3 ---")

        # Step 2: Visit each page and extract/download the image
        for link in links:
            print(f"Processing: {link}")
            image_url = extract_image_url(link)
            if image_url:
                download_image(image_url)

        if cycle < 2:  # Wait only after the first and second cycles (not after the last one)
            print("\nWaiting for 5 minutes before the next cycle...\n")
            time.sleep(300)  # Wait for 5 minutes (300 seconds)

if __name__ == "__main__":
    if DEBUG:
        print(f"Checking directories:\nTraining: {TRAINING_DIR}\nTesting: {TESTING_DIR}")
    
    main()
