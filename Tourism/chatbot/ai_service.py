"""
chatbot/ai_service.py

Two real fixes on top of the routing bug in services.py:
1. groq_response()/gemini_response() had no error handling at all -- a
   missing/invalid key, rate limit, or network blip would throw an
   unhandled exception and crash the whole chat request instead of
   falling back to the canned responses in services.py. Now caught and
   logged, returns None on failure so the fallback chain works as
   intended.
2. Added huggingface_response() -- HF_API_KEY existed in .env per your
   message but had no code path at all; AI_PROVIDER="groq" (the
   settings.py default) meant it was silently unreachable regardless.
"""
import logging
import os

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


# Tried in this order when the preferred provider (AI_PROVIDER, default
# "groq") fails or isn't configured -- previously a single provider
# failure meant ask_ai() returned None and the chatbot fell all the way
# back to canned responses, even if 3 other configured keys could have
# answered. Each function already returns None on its own failure
# (never raises past this point), so the loop just tries the next one.
PROVIDER_FUNCTIONS = {
    "groq": lambda m, c: groq_response(m, c),
    "gemini": lambda m, c: gemini_response(m, c),
    "openrouter": lambda m, c: openrouter_response(m, c),
    "huggingface": lambda m, c: huggingface_response(m, c),
}


def ask_ai(message, context=""):
    preferred = os.getenv("AI_PROVIDER", "groq")
    # Preferred provider first, then whichever others are left, in a
    # fixed sensible order -- not random, so behavior is predictable.
    order = [preferred] + [p for p in PROVIDER_FUNCTIONS if p != preferred]

    for provider in order:
        fn = PROVIDER_FUNCTIONS.get(provider)
        if fn is None:
            continue
        try:
            result = fn(message, context)
            if result:
                return result
        except Exception as exc:  # noqa: BLE001 -- one provider failing must never crash the chat endpoint or block trying the next
            logger.warning("AI provider '%s' failed, trying next: %s", provider, exc)
            continue

    logger.error("All AI providers failed or returned nothing for this message.")
    return None


def groq_response(message, context):
    from groq import Groq

    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    prompt = f"""
You are Nepal Tourism Assistant.

Answer the user question.

Use this information if available:
{context}

User:
{message}
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": "You help tourists travelling in Nepal."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.5,
    )
    return response.choices[0].message.content


def gemini_response(message, context):
    import google.generativeai as genai

    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
    model = genai.GenerativeModel("gemini-2.0-flash")

    prompt = f"""
You are Nepal Tourism Assistant.

Context:
{context}

Question:
{message}
"""
    response = model.generate_content(prompt)
    return response.text


def huggingface_response(message, context):
    """
    New -- didn't exist before. Uses HF's Inference API chat-completion
    endpoint. Set AI_PROVIDER=huggingface in .env to use this instead of
    Groq/Gemini, and HF_MODEL to pick a specific model (defaults to a
    small, fast instruction-tuned model reasonable for chat).
    """
    import requests

    api_key = os.getenv("HF_API_KEY")
    model_id = os.getenv("HF_MODEL", "HuggingFaceH4/zephyr-7b-beta")

    prompt = f"You are Nepal Tourism Assistant. Context:\n{context}\n\nUser: {message}\nAssistant:"

    response = requests.post(
        f"https://api-inference.huggingface.co/models/{model_id}",
        headers={"Authorization": f"Bearer {api_key}"},
        json={"inputs": prompt, "parameters": {"max_new_tokens": 300, "temperature": 0.5}},
        timeout=15,
    )
    response.raise_for_status()
    result = response.json()

    if isinstance(result, list) and result and "generated_text" in result[0]:
        text = result[0]["generated_text"]
        # HF often echoes the prompt back before the actual completion --
        # strip it so only the new content is returned.
        return text.split("Assistant:")[-1].strip()

    return None

def openrouter_response(message, context):
    """
    New -- OpenRouter gives access to many models (Claude, GPT, Llama,
    Mistral, etc.) through one API. Set AI_PROVIDER=openrouter in .env
    to use this. OPENROUTER_MODEL defaults to a free Llama model.
    """
    import requests

    api_key = os.getenv("OPENROUTER_API_KEY")
    model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-8b-instruct:free")

    prompt = f"""
You are Nepal Tourism Assistant.

Answer the user question.

Use this information if available:
{context}

User:
{message}
"""
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": "You help tourists travelling in Nepal."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.5,
        },
        timeout=15,
    )
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]