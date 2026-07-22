from fastapi import APIRouter
from pydantic import BaseModel

from model.translation.translation_engine import translate

router = APIRouter()


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"  # "en" or "ne"


@router.post("/translate")
def post_translate(payload: TranslateRequest):
    return translate(payload.text, payload.target_lang)