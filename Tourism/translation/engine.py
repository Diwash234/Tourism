"""
translation/engine.py

Extracted from tourist/utils.py's translation section -- same logic,
moved into its own app so `tourist` isn't the single dumping ground for
every unrelated feature. Public behavior is unchanged: same tiers, same
provider param, same fallback order.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

# Translation
# ---------------------------------------------------------------------------
def _translate_via_openai(text, target_language, source_language):
    """
    Returns translated text via the OpenAI API, or None if not configured/
    unreachable. Used as the first-choice translation tier when
    OPENAI_API_KEY is set — generally higher quality than Google Translate
    for nuanced tourism copy (descriptions, alerts), at a per-call cost.
    """
    if not settings.OPENAI_API_KEY:
        return None
    try:
        source_note = "" if source_language == "auto" else f" (source language: {source_language})"
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENAI_API_KEY}"},
            json={
                "model": settings.OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"Translate the user's text into the language with ISO code "
                            f"'{target_language}'{source_note}. Reply with ONLY the translated "
                            f"text, no explanations, no quotes."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                "temperature": 0.2,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning("OpenAI translation failed, falling back: %s", exc)
        return None


def _translate_via_ml_service(text, target_language, source_language):
    """Returns translated text from the ML service, or None if unreachable/not yet trained."""
    try:
        response = requests.post(
            f"{settings.ML_SERVICE_URL}/translation/translate-custom",
            json={"text": text, "target_language": target_language, "source_language": source_language},
            timeout=settings.ML_SERVICE_TIMEOUT,
        )
        response.raise_for_status()
        translated = response.json().get("translated_text")
        # The ML service's pass-through fallback returns the text unchanged
        # when no local model is loaded yet — treat that as "not handled"
        # so we still fall through to Google/deep-translator.
        return translated if translated and translated != text else None
    except requests.RequestException as exc:
        logger.info("ML translation service unreachable, falling back: %s", exc)
        return None



def _translate_via_gemini(text, target_language, source_language):
    """
    Returns translated text via Google's Gemini API, or None if not
    configured/unreachable. Same shape as _translate_via_openai --
    slots into the same tiered chain.
    """
    if not settings.GEMINI_API_KEY:
        return None
    try:
        source_note = "" if source_language == "auto" else f" (source language: {source_language})"
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{settings.GEMINI_MODEL}:generateContent",
            params={"key": settings.GEMINI_API_KEY},
            json={
                "contents": [{
                    "parts": [{
                        "text": (
                            f"Translate the following text into the language with ISO code "
                            f"'{target_language}'{source_note}. Reply with ONLY the translated "
                            f"text, no explanations, no quotes.\n\n{text}"
                        )
                    }]
                }],
                "generationConfig": {"temperature": 0.2},
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning("Gemini translation failed, falling back: %s", exc)
        return None


def _translate_via_groq(text, target_language, source_language):
    """
    Returns translated text via Groq's chat completion API (OpenAI-compatible
    format), or None if not configured/unreachable.
    """
    if not settings.GROQ_API_KEY:
        return None
    try:
        source_note = "" if source_language == "auto" else f" (source language: {source_language})"
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={
                "model": settings.GROQ_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            f"Translate the user's text into the language with ISO code "
                            f"'{target_language}'{source_note}. Reply with ONLY the translated "
                            f"text, no explanations, no quotes."
                        ),
                    },
                    {"role": "user", "content": text},
                ],
                "temperature": 0.2,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning("Groq translation failed, falling back: %s", exc)
        return None


def translate_text(text, target_language, source_language="auto", provider="auto"):
    """
    Translate `text` into `target_language`.

    provider: "auto" (default -- tiered fallback below), or an explicit
        choice: "gemini", "groq", "openai" (all three = "AI-enhanced
        contextual translation" per the original spec), or "standard"
        (skips straight to Google/deep-translator, no AI model involved).

    Automatic tiers, tried in order when provider="auto":
      1. Gemini (if GEMINI_API_KEY is configured)
      2. Groq (if GROQ_API_KEY is configured)
      3. OpenAI (if OPENAI_API_KEY is configured) — generally the highest
         quality for nuanced tourism copy (descriptions, alerts).
      4. The ML teammate's local-language model (`{ML_SERVICE_URL}/translate-custom`),
         for languages Google Translate handles poorly (e.g. underrepresented
         local languages) — see ml-service/model/translation_engine.py.
         Tried before Google/deep-translator for languages listed in
         LOCAL_TRANSLATION_LANGUAGE_CODES (set in settings).
      5. Google Cloud Translation API, if GOOGLE_TRANSLATE_API_KEY is configured.
      6. The free deep-translator (Google Translate) library — always available,
         no credentials needed, so translation never fully breaks.
    """
    if not text:
        return text

    if provider == "standard":
        pass  # skip straight past all AI tiers below
    elif provider in ("gemini", "groq", "openai"):
        result = {
            "gemini": _translate_via_gemini,
            "groq": _translate_via_groq,
            "openai": _translate_via_openai,
        }[provider](text, target_language, source_language)
        if result is not None:
            return result
        # Explicit provider failed/unconfigured -- fall through to the
        # rest of the chain rather than returning nothing.
    else:
        gemini_result = _translate_via_gemini(text, target_language, source_language)
        if gemini_result is not None:
            return gemini_result

        groq_result = _translate_via_groq(text, target_language, source_language)
        if groq_result is not None:
            return groq_result

        openai_result = _translate_via_openai(text, target_language, source_language)
        if openai_result is not None:
            return openai_result

    use_local_first = target_language in settings.LOCAL_TRANSLATION_LANGUAGE_CODES
    if use_local_first:
        local_result = _translate_via_ml_service(text, target_language, source_language)
        if local_result is not None:
            return local_result

    if settings.GOOGLE_TRANSLATE_API_KEY:
        try:
            response = requests.post(
                "https://translation.googleapis.com/language/translate/v2",
                params={"key": settings.GOOGLE_TRANSLATE_API_KEY},
                data={
                    "q": text,
                    "target": target_language,
                    "source": None if source_language == "auto" else source_language,
                    "format": "text",
                },
                timeout=5,
            )
            response.raise_for_status()
            return response.json()["data"]["translations"][0]["translatedText"]
        except (requests.RequestException, KeyError, IndexError) as exc:
            logger.warning("Google Translate API failed, falling back: %s", exc)

    if not use_local_first:
        # Wasn't tried yet above — try it now as a second-to-last resort.
        local_result = _translate_via_ml_service(text, target_language, source_language)
        if local_result is not None:
            return local_result

    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source=source_language, target=target_language).translate(text)
    except Exception as exc:  # noqa: BLE001 - translation is best-effort
        logger.error("Translation fallback failed: %s", exc)
        return text