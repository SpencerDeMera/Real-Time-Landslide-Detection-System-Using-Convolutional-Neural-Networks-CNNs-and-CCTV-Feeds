import os
import random
import pandas as pd
from sklearn.model_selection import train_test_split

LANDSLIDE_DIR = "/mnt/c/Users/spenc/Desktop/CpE-Projects/GradProject/RAW_CCTV_Images/landslides"
NORMAL_DIR = "/mnt/c/Users/spenc/Desktop/CpE-Projects/GradProject/RAW_CCTV_Images/standard"
CSV_PATH = "/mnt/c/Users/spenc/Desktop/CpE-Projects/GradProject/initialCSVLabels.csv"

TRAIN_CSV_PATH = "/mnt/c/Users/spenc/Desktop/CpE-Projects/GradProject/initialLabeledTrain.csv"
TEST_CSV_PATH = "/mnt/c/Users/spenc/Desktop/CpE-Projects/GradProject/initialLabeledTest.csv"

# Ensure directories exist
os.makedirs(os.path.dirname(CSV_PATH), exist_ok=True)
os.makedirs(os.path.dirname(TRAIN_CSV_PATH), exist_ok=True)
os.makedirs(os.path.dirname(TEST_CSV_PATH), exist_ok=True)

# Create labels
data = []

# Assign label 0 for normal road images
for img_name in os.listdir(NORMAL_DIR):
    img_path = os.path.join(NORMAL_DIR, img_name)
    if os.path.isfile(img_path):  # Ensure it's a file
        data.append({"file_path": img_path, "label": 0})

# Assign label 1 for landslide images
for img_name in os.listdir(LANDSLIDE_DIR):
    img_path = os.path.join(LANDSLIDE_DIR, img_name)
    if os.path.isfile(img_path):  # Ensure it's a file
        data.append({"file_path": img_path, "label": 1})

# Save to CSV
df = pd.DataFrame(data)
df.to_csv(CSV_PATH, index=False)

print(f"CSV saved to: {CSV_PATH}")

# Split dataset
train, test = train_test_split(df, test_size=0.2, random_state=42)

# Save splits
train.to_csv(TRAIN_CSV_PATH, index=False)
test.to_csv(TEST_CSV_PATH, index=False)

print(f"Dataset split completed: {TRAIN_CSV_PATH}, {TEST_CSV_PATH}")