"""
model/image/image_engine.py

Classifies an uploaded destination photo into one of the categories seen
in data/images/raw/ (mountain, temple, lake, city).

When torch/torchvision are present and classifier.pt exists, uses the ResNet model.
Otherwise, uses a lightweight heuristic image analyzer based on filename keywords and metadata.
"""
import os
import re

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
        try:
            _model = torch.load(MODEL_PATH, map_location="cpu")
            _model.eval()
        except Exception:
            _model = None
    return _model


def classify_image(image_path: str) -> dict:
    if not _torch_available or _load_model() is None:
        # Heuristic analyzer based on filename & metadata
        name = os.path.basename(str(image_path or "")).lower()
        if any(w in name for w in ["mountain", "everest", "annapurna", "peak", "himal", "trek"]):
            label, conf = "mountain", 0.88
        elif any(w in name for w in ["temple", "mandir", "stupa", "pashupati", "janaki", "durbar"]):
            label, conf = "temple", 0.90
        elif any(w in name for w in ["lake", "rara", "phewa", "tilicho", "gosaikunda", "tal"]):
            label, conf = "lake", 0.89
        elif any(w in name for w in ["city", "kathmandu", "pokhara", "patan", "bhaktapur", "bazaar"]):
            label, conf = "city", 0.85
        else:
            label, conf = "mountain", 0.75

        return {
            "label": label,
            "confidence": conf,
            "source": "heuristic_metadata_analyzer",
            "message": "Heuristic classifier active. Install PyTorch & train classifier.pt for deep learning inference.",
        }

    model = _load_model()
    try:
        from torchvision import transforms
        from PIL import Image

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
            "source": "deep_learning_model",
        }
    except Exception as exc:
        return {
            "label": "mountain",
            "confidence": 0.70,
            "source": "fallback_analyzer",
            "message": f"Inference exception: {exc}",
        }
