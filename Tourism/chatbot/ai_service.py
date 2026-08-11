import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

NEPAL_SYSTEM_PROMPT = """You are Himal AI, the intelligent, friendly, and authoritative Nepal Tourism Assistant.
You provide helpful, concise, and accurate advice to travelers exploring Nepal.

Your core expertise includes:
1. Top Destinations: Kathmandu Valley (Pashupatinath, Boudhanath, Swayambhunath, Durbar Squares), Pokhara (Phewa Lake, Sarangkot, World Peace Pagoda), Annapurna Region (ABC, Poon Hill, Circuit, Tilicho), Everest Region (EBC, Namche Bazaar, Gokyo), Chitwan & Bardiya Wildlife Safaris, Lumbini (Birthplace of Lord Buddha), Rara Lake, Langtang Valley, Mustang/Muktinath, Bandipur, Ilam tea gardens, Janakpurdham.
2. Treks & Permits: TIMS card, ACAP, MCAP, Sagarmatha National Park entry, restricted area permits for Upper Mustang/Manaslu/Dolpo. Altitude sickness precautions (acclimatization days, hydration, Diamox, descending on AMS symptoms).
3. Travel Budgets: Backpacker ($20-$35/day or NPR 2,500-4,500), Mid-range ($40-$80/day or NPR 5,000-10,500), Luxury ($100+/day or NPR 13,000+). Local currency is Nepalese Rupee (NPR).
4. Safety & Emergency:
   - Tourist Police: 1144 or +977-1-4247041
   - Nepal Police: 100
   - Ambulance: 102
   - Fire Service: 101
   - Traffic Police: 103
5. Seasons & Weather:
   - Peak Autumn (Sep-Nov): Crystal clear mountain views, best trekking.
   - Spring (Mar-May): Blooming rhododendrons, warm days.
   - Monsoon (Jun-Aug): Lush greenery, risk of landslides on highways, best time for rain-shadow areas (Mustang, Upper Dolpo).
   - Winter (Dec-Feb): Chilly in Himalayas, excellent for Terai/Chitwan/Pokhara.
6. Cultural Etiquette & Greetings: "Namaste" with palms joined, remove shoes before entering temples/homes, walk clockwise around Buddhist stupas and chortens.

Respond politely, format with clear bullet points and emojis where helpful."""


def ask_ai(message: str, context: str = "", history: list = None) -> str:
    """
    Attempts calling configured AI providers in order of availability:
    1. Grok (xAI)
    2. Gemini (Google)
    3. Groq (Llama-3)
    4. Hugging Face
    5. OpenAI
    6. Smart Local Knowledge Engine fallback
    """
    # 1. Try Grok (xAI)
    grok_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
    if grok_key:
        try:
            reply = call_grok(message, context, grok_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning(f"Grok API failed: {e}")

    # 2. Try Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            reply = call_gemini(message, context, gemini_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning(f"Gemini API failed: {e}")

    # 3. Try Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            reply = call_groq(message, context, groq_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning(f"Groq API failed: {e}")

    # 4. Try Hugging Face
    hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN")
    if hf_key:
        try:
            reply = call_huggingface(message, context, hf_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning(f"Hugging Face API failed: {e}")

    # 5. Try OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            reply = call_openai(message, context, openai_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning(f"OpenAI API failed: {e}")

    # 6. Fallback to smart rule-based engine
    return None


def call_grok(message: str, context: str, api_key: str) -> str:
    url = "https://api.x.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    user_prompt = f"Context:\n{context}\n\nQuestion: {message}" if context else message
    payload = {
        "model": "grok-2-latest",
        "messages": [
            {"role": "system", "content": NEPAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.6,
        "max_tokens": 800,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    return None


def call_gemini(message: str, context: str, api_key: str) -> str:
    # Use direct REST endpoint to avoid SDK incompatibility
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    headers = {"Content-Type": "application/json"}
    prompt_text = f"{NEPAL_SYSTEM_PROMPT}\n\nContext:\n{context}\n\nUser Question: {message}" if context else f"{NEPAL_SYSTEM_PROMPT}\n\nUser Question: {message}"
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt_text}
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.5,
            "maxOutputTokens": 800,
        }
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        candidates = data.get("candidates", [])
        if candidates and "content" in candidates[0]:
            parts = candidates[0]["content"].get("parts", [])
            if parts:
                return parts[0].get("text", "").strip()
    return None


def call_groq(message: str, context: str, api_key: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    user_prompt = f"Context:\n{context}\n\nQuestion: {message}" if context else message
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": NEPAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 800,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    return None


def call_huggingface(message: str, context: str, api_key: str) -> str:
    # Router or serverless inference endpoint
    url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    prompt_text = f"<s>[INST] {NEPAL_SYSTEM_PROMPT}\n\n{context}\n\n{message} [/INST]"
    payload = {
        "inputs": prompt_text,
        "parameters": {
            "max_new_tokens": 500,
            "temperature": 0.6,
            "return_full_text": False,
        }
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=12)
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, list) and len(data) > 0:
            return data[0].get("generated_text", "").strip()
    return None


def call_openai(message: str, context: str, api_key: str) -> str:
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    user_prompt = f"Context:\n{context}\n\nQuestion: {message}" if context else message
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "system", "content": NEPAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 800,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    return None
