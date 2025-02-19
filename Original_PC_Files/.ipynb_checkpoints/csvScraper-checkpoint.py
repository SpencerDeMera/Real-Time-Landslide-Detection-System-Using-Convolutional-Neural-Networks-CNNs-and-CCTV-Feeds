import os
import uuid
import pandas as pd
import requests
import urllib.request
from PIL import Image, ImageEnhance
from urllib.parse import urljoin, urlparse

# Load CSV
CSV_FILE = "/mnt/c/Users/spenc/Desktop/CpE-Projects/GradProject/Global_Landslide_Catalog_Export.csv"  # Update this with your CSV path
IMAGE_FOLDER = "/mnt/c/Users/spenc/Desktop/CpE-Projects/GradProject/RAW_CCTV_Images/landslides"  # Folder to save images
BASE_DIR = os.path.abspath(IMAGE_FOLDER)  # Absolute path for storage

# Read CSV
df = pd.read_csv(CSV_FILE)

# Ensure column exists
if "photo_link" not in df.columns:
    raise ValueError("Column 'photo_link' not found in CSV")

# Function to create directories
def assign_directory():
    directory = os.path.join(BASE_DIR)
    os.makedirs(directory, exist_ok=True)
    return directory

# Function to save images
def save_image(image_path, image):
    try:
        image.save(image_path)
        print(f"Saved: {image_path}")
    except Exception as e:
        print(f"Error saving {image_path}: {e}")

# Function to process images
def process_image(image_path):
    try:
        image = Image.open(image_path)
        
        # Resize image to 320x260
        image = image.resize((320,260), Image.ANTIALIAS)

        # Assign directories for each variation
        original_dir = assign_directory()
        flipped_dir = assign_directory()
        rotated_dir = assign_directory()
        darkened_dir = assign_directory()
        brightened_dir = assign_directory()

        # Generate base filename
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

        # Save original image
        save_image(original_save_path, image)

        # Flipped image
        flipped_image = image.transpose(Image.FLIP_LEFT_RIGHT)
        save_image(flipped_save_path, flipped_image)

        # Rotated image
        rotated_image = image.rotate(180)
        save_image(rotated_save_path, rotated_image)

        # Darkened image
        enhancer = ImageEnhance.Brightness(image)
        darkened_image = enhancer.enhance(0.5)
        save_image(darkened_save_path, darkened_image)

        # Brightened image
        brightened_image = enhancer.enhance(1.5)
        save_image(brightened_save_path, brightened_image)

    except Exception as e:
        print(f"Error processing {image_path}: {e}")

# Function to download and process image
def download_image(image_url):
    if not image_url or not isinstance(image_url, str) or not image_url.startswith("http"):
        print(f"Skipping invalid URL: {image_url}")
        return

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}.jpg"
    temp_path = os.path.join(BASE_DIR, unique_filename)

    try:
        response = requests.get(image_url, stream=True, timeout=10)
        if response.status_code == 200:
            with open(temp_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Downloaded: {temp_path}")

            # Process the image
            process_image(temp_path)

            # Remove temp file after processing
            os.remove(temp_path)

        else:
            print(f"Failed to download (404 or other error): {image_url}")

    except Exception as e:
        print(f"Error downloading {image_url}: {e}")

# Process each valid image link in CSV
for url in df["photo_link"].dropna().unique():  # Remove NaN and duplicate URLs
    download_image(url)

print("Image processing completed.")
