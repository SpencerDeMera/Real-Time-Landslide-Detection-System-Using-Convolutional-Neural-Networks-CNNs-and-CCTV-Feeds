import os
from PIL import Image
import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Activation, Dropout

DEBUG = True

if DEBUG:
    print("Debugging Enabled...")
    print(tf.config.list_physical_devices('GPU'))

CSV_PATH = 'CSV_Data/initialCSVLabels.csv'
TRAIN_CSV_PATH = 'initialLabeledTrain.csv'
TEST_CSV_PATH = 'initialLabeledTest.csv'

numpySaves = "/mnt/c/Users/spenc/Desktop/CpE-Projects/GradProject/NumPyDataSaves"
os.makedirs(numpySaves, exist_ok=True)

ImgSize = (320,260)
NumClasses = 2  # Binary classification: normal (0) vs landslide (1)
BatchSize = 128
EpochNum = 50

trainDataFrame = pd.read_csv(TRAIN_CSV_PATH)
testDataFrame = pd.read_csv(TEST_CSV_PATH)

allResults = [] # to store results of all the runs

def loadAndPreprocessImage(path):
    try:
        img = Image.open(path).convert("RGB")  # Load image with PIL
        img = np.array(img, dtype=np.float32) / 255.0  # Normalize
        return img
    except Exception as e:
        print(f"Skipping invalid image: {path} - Error: {e}")
        return None

# Load images and labels
if DEBUG:
    print("Loading and preprocessing training images...")
trainImages = np.array([loadAndPreprocessImage(path) for path in trainDataFrame["file_path"]])
    
if DEBUG:
    print("Extracting training labels...")
trainLabels = np.array(train_df["label"])
    
if DEBUG:
    print("Loading and preprocessing test images...")
testImages = np.array([loadAndPreprocessImage(path) for path in testDataFrame["file_path"]])
    
if DEBUG:
    print("Extracting test labels...")
testLabels = np.array(test_df["label"])

# Convert labels to one-hot encoding (for softmax classification)
trainLabels = to_categorical(trainLabels, num_classes=NumClasses)
testLabels = to_categorical(testLabels, num_classes=NumClasses)

# Split training data further into train and validation sets
if DEBUG:
    print("Generating validation images and labels...")
trainImages, valImages, trainLabels, valLabels = train_test_split(trainImages, trainLabels, test_size=0.2, random_state=42)

if DEBUG:
    print("Saving numpy array data...")
# Save training data
np.save(os.path.join(numpySaves, "trainImages.npy"), trainImages)
np.save(os.path.join(numpySaves, "trainLabels.npy"), trainLabels)
# Save validation data
np.save(os.path.join(numpySaves, "valImages.npy"), valImages)
np.save(os.path.join(numpySaves, "valLabels.npy"), valLabels)
# Save test data
np.save(os.path.join(numpySaves, "testImages.npy"), testImages)
np.save(os.path.join(numpySaves, "testLabels.npy"), testLabels)

if DEBUG:
    print(f"Train: {trainImages.shape}, {trainLabels.shape}")
    print(f"Validation: {valImages.shape}, {valLabels.shape}")
    print(f"Test: {testImages.shape}, {testLabels.shape}")
