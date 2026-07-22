"""
training/train_image_classifier.py

Fine-tunes a small CNN (resnet18 transfer learning) to classify a photo
into one of: mountain, temple, lake, city - matching data/images/raw/.

NOT RUN YET in this deliverable, on purpose: it needs real labeled
photos in data/images/raw/<category>/*.jpg (plus data/images/labels.csv)
and torch/torchvision installed, neither of which exist here. Training
on empty folders would only produce random, meaningless weights, so
model/image/classifier.pt is intentionally left out until you supply
real images - image_engine.py already returns a clear "not trained yet"
response in the meantime instead of failing silently.

Run once you have images in place:
    pip install torch torchvision
    python training/train_image_classifier.py
"""
import os
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from torchvision import datasets, transforms, models

DATA_DIR = "data/images/raw"          # expects one subfolder per category
MODEL_OUT = "model/image/classifier.pt"
CATEGORIES = ["mountain", "temple", "lake", "city"]
EPOCHS = 5
BATCH_SIZE = 16


def main():
    if not os.path.isdir(DATA_DIR) or not any(os.scandir(DATA_DIR)):
        print(f"No images found under {DATA_DIR}/<category>/*.jpg - add real photos first.")
        return

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    dataset = datasets.ImageFolder(DATA_DIR, transform=transform)
    loader = DataLoader(dataset, batch_size=BATCH_SIZE, shuffle=True)

    model = models.resnet18(weights="IMAGENET1K_V1")
    model.fc = nn.Linear(model.fc.in_features, len(CATEGORIES))

    optimizer = torch.optim.Adam(model.parameters(), lr=1e-4)
    criterion = nn.CrossEntropyLoss()

    model.train()
    for epoch in range(EPOCHS):
        running_loss = 0.0
        for images, labels in loader:
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item()
        print(f"Epoch {epoch + 1}/{EPOCHS} - loss: {running_loss / len(loader):.4f}")

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    torch.save(model, MODEL_OUT)
    print(f"Saved classifier to {MODEL_OUT}")


if __name__ == "__main__":
    main()