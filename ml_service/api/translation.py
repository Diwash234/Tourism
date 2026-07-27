from fastapi import APIRouter
from pydantic import BaseModel

from model.translation.translation_engine import translate

router = APIRouter()


class TranslateRequest(BaseModel):
    text: str
    target_lang: str = "en"  # "en" or "ne"
    target_language: str | None = None
    source_language: str = "auto"


@router.post("/translate")
def post_translate(payload: TranslateRequest):
    return translate(payload.text, payload.target_language or payload.target_lang)


@router.post("/translate-custom")
def translate_custom(payload: TranslateRequest):
    result = translate(payload.text, payload.target_language or payload.target_lang)
    return {
        "translated_text": result.get("translation"),
        "source": result.get("source"),
        "message": result.get("message"),
    }