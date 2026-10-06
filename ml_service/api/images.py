import os
import tempfile

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter()
MAX_IMAGE_UPLOAD_BYTES = 10 * 1024 * 1024


@router.post("/classify")
async def classify(file: UploadFile = File(...)):
    suffix = os.path.splitext(file.filename)[1] or ".jpg"
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp_path = tmp.name
            total = 0
            while chunk := await file.read(1024 * 1024):
                total += len(chunk)
                if total > MAX_IMAGE_UPLOAD_BYTES:
                    raise HTTPException(status_code=413, detail="Image exceeds the 10 MiB upload limit.")
                tmp.write(chunk)

        # Importing the classifier must not import PyTorch for every ML API
        # process; the classifier itself only loads it if a trained model exists.
        from model.image.image_engine import classify_image

        result = classify_image(tmp_path)
    finally:
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)
        await file.close()

    return result