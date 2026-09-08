"""
translation/engine.py

Extracted from tourist/utils.py's translation section, PLUS the Gemini/
Groq functions added here for the first time -- settings.py already has
GEMINI_API_KEY/GROQ_API_KEY wired (config() calls exist), but nothing
ever actually called them; translate_text() only had OpenAI + Google/
deep-translator tiers. Fixed as part of this extraction.
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
    """Returns translated text via Google's Gemini API, or None if not configured/unreachable."""
    if not settings.GEMINI_API_KEY:
        return None
    try:
        source_note = "" if source_language == "auto" else f" (source language: {source_language})"
        response = requests.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{getattr(settings, 'GEMINI_MODEL', 'gemini-1.5-flash')}:generateContent",
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
    """Returns translated text via Groq's chat completion API, or None if not configured/unreachable."""
    if not settings.GROQ_API_KEY:
        return None
    try:
        source_note = "" if source_language == "auto" else f" (source language: {source_language})"
        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}"},
            json={
                "model": getattr(settings, "GROQ_MODEL", "llama-3.1-8b-instant"),
                "messages": [
                    {"role": "system", "content": (
                        f"Translate the user's text into the language with ISO code "
                        f"'{target_language}'{source_note}. Reply with ONLY the translated "
                        f"text, no explanations, no quotes."
                    )},
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


def _translate_via_openrouter(text, target_language, source_language):
    """Returns translated text via OpenRouter (access to Claude/GPT/Llama/etc. through one API), or None if not configured/unreachable."""
    if not settings.OPENROUTER_API_KEY:
        return None
    try:
        source_note = "" if source_language == "auto" else f" (source language: {source_language})"
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {settings.OPENROUTER_API_KEY}"},
            json={
                "model": settings.OPENROUTER_MODEL,
                "messages": [
                    {"role": "system", "content": (
                        f"Translate the user's text into the language with ISO code "
                        f"'{target_language}'{source_note}. Reply with ONLY the translated "
                        f"text, no explanations, no quotes."
                    )},
                    {"role": "user", "content": text},
                ],
                "temperature": 0.2,
            },
            timeout=10,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except (requests.RequestException, KeyError, IndexError) as exc:
        logger.warning("OpenRouter translation failed, falling back: %s", exc)
        return None


def translate_text(text, target_language, source_language="auto", provider="auto"):
    """
    Translate `text` into `target_language`.

    provider: "auto" (default -- tiered fallback below), or an explicit
        choice: "gemini", "groq", "openai", or "standard" (skips
        straight to Google/deep-translator, no AI model).

    Automatic tiers when provider="auto":
      1. Gemini (if GEMINI_API_KEY is configured)
      2. Groq (if GROQ_API_KEY is configured)
      3. OpenAI (if OPENAI_API_KEY is configured)
      4. The ML teammate's local-language model, for languages listed in
         LOCAL_TRANSLATION_LANGUAGE_CODES.
      5. Google Cloud Translation API, if GOOGLE_TRANSLATE_API_KEY is configured.
      6. The free deep-translator library — always available, so
         translation never fully breaks.
    """
    if not text:
        return text

    if provider == "standard":
        pass
    elif provider in ("gemini", "groq", "openai", "openrouter"):
        result = {
            "gemini": _translate_via_gemini,
            "groq": _translate_via_groq,
            "openai": _translate_via_openai,
            "openrouter": _translate_via_openrouter,
        }[provider](text, target_language, source_language)
        if result is not None:
            return result
    else:
        gemini_result = _translate_via_gemini(text, target_language, source_language)
        if gemini_result is not None:
            return gemini_result

        groq_result = _translate_via_groq(text, target_language, source_language)
        if groq_result is not None:
            return groq_result

        openrouter_result = _translate_via_openrouter(text, target_language, source_language)
        if openrouter_result is not None:
            return openrouter_result

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





import json


def generate_destination_content(name, city=None, country="Nepal", existing_description=""):
    """
    Uses whichever AI provider is configured (same priority as
    translate_text) to draft a description + best_time_to_visit for a
    destination missing them. Returns None if nothing is configured or
    every provider fails -- caller decides what to do, never returns
    fake content.
    """
    location = f"{name}" + (f", {city}" if city else "") + f", {country}"

    prompt = (
        f"Write tourism content for the destination: {location}.\n"
        + (f"Existing description to improve/expand rather than replace: {existing_description}\n" if existing_description else "")
        + "Respond as JSON only, no markdown formatting, no explanation, with exactly these keys:\n"
        + '{"description": "2-3 sentence factual, engaging description", '
        + '"short_description": "one sentence, under 150 characters", '
        + '"best_time_to_visit": "e.g. October to December, and March to April"}'
    )

    for provider_fn in [_translate_via_gemini, _translate_via_groq, _translate_via_openrouter, _translate_via_openai]:
        try:
            raw = provider_fn(prompt, "en", "en")
        except Exception as exc:
            logger.warning("Content generation via a provider failed: %s", exc)
            raw = None

        if raw:
            try:
                cleaned = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
                data = json.loads(cleaned)
                if "description" in data:
                    return data
            except (json.JSONDecodeError, AttributeError):
                continue

    return None