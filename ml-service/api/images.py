import os
import tempfile

from fastapi import APIRouter, UploadFile, File

from model.image.image_engine import classify_image

router = APIRouter()


@router.post("/classify")
async def classify(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        result = classify_image(tmp_path)
    finally:
        os.remove(tmp_path)

    return result