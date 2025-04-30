import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from django.conf import settings
import os

class CNN(nn.Module):
    def __init__(self):
        super(CNN, self).__init__()
        self.conv1 = nn.Conv2d(3, 32, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(32, 64, kernel_size=3, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.fc1 = nn.Linear(64 * 65 * 80, 512)  # Adjusted for (260, 320) input size
        self.fc2 = nn.Linear(512, 27)  # Adjust output size

    def forward(self, x):
        x = self.pool(F.relu(self.conv1(x)))
        x = self.pool(F.relu(self.conv2(x)))
        x = x.view(x.size(0), -1)  # Flatten
        x = F.relu(self.fc1(x))
        x = self.fc2(x)
        return x

# Load the model
def loadModel():
    model = CNN()
    model_path = os.path.join(os.path.dirname(__file__), 'assets', 'savedModels', 'bestModel_2025-03-02.pth')
    model.load_state_dict(torch.load(model_path, map_location=torch.device("cpu")))
    model.eval()
    return model

# Define the image transformation
def getTransform():
    return transforms.Compose([
        transforms.Resize((260, 320)),
        transforms.ToTensor(),
    ])