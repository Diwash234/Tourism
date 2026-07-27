"""
model/image/image_engine.py

Classifies an uploaded destination photo into one of the categories seen
in data/images/raw/ (mountain, temple, lake, city).

torch/torchvision are NOT in the default requirements.txt because they're
heavy - install them (see requirements.txt comments) once you're ready to
train classifier.pt with training/train_image_classifier.py. Until then,
this engine returns a clearly-labeled placeholder response instead of
crashing the API.
"""
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), "classifier.pt")
CATEGORIES = ["mountain", "temple", "lake", "city"]

_torch_available = False
_model = None

try:
    import torch
    from torchvision import transforms
    from PIL import Image

    _torch_available = True
except ImportError:
    pass


def _load_model():
    global _model
    if _model is not None or not _torch_available:
        return _model
    if os.path.exists(MODEL_PATH):
        _model = torch.load(MODEL_PATH, map_location="cpu")
        _model.eval()
    return _model


def classify_image(image_path: str) -> dict:
    if not _torch_available:
        return {
            "label": None,
            "confidence": None,
            "source": "unavailable",
            "message": "torch/torchvision not installed - see requirements.txt comments",
        }

    model = _load_model()
    if model is None:
        return {
            "label": None,
            "confidence": None,
            "source": "unavailable",
            "message": "classifier.pt not found - run training/train_image_classifier.py first",
        }

    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
    ])
    img = Image.open(image_path).convert("RGB")
    tensor = transform(img).unsqueeze(0)

    with torch.no_grad():
        outputs = model(tensor)
        probs = torch.softmax(outputs, dim=1)[0]
        top_idx = int(torch.argmax(probs))

    return {
        "label": CATEGORIES[top_idx],
        "confidence": round(float(probs[top_idx]), 3),
        "source": "model",
    }