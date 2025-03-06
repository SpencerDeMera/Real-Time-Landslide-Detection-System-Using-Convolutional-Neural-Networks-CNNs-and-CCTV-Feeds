from fastapi import FastAPI, File, UploadFile
import torch
import torch.nn as nn
import torch.nn.functional as F
from torchvision import transforms
from PIL import Image
import io

# Start Server
# uvicorn server:app --host 0.0.0.0 --port 8000

# CNN model structure from trained model
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

model = CNN()

# Imported trained model weights
model.load_state_dict(torch.load("../ModelSaves/bestModel_2025-03-02.pth", map_location=torch.device("cpu")))
model.eval()

# compose and tranform data to correctly sized tensors
transform = transforms.Compose([
    transforms.Resize((260, 320)),
    transforms.ToTensor(),
])

app = FastAPI()

# Prediction endpoint
@app.post("/predict/")
async def predict(file: UploadFile = File(...)):
    # Read image
    image_bytes = await file.read()
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")  # Convert to RGB

    # Apply transformations
    image = transform(image).unsqueeze(0)  # Add batch dimension

    # Make prediction
    with torch.no_grad():
        output = model(image)
        probabilities = F.softmax(output, dim=1)
        prediction = torch.argmax(probabilities, dim=1).item()

    return prediction