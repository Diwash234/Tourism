"""
Tourism/chatbot/ai_service.py

Multi-model AI Orchestrator for Himal AI Nepal Tourism Assistant.
Connects with OpenRouter, Grok (xAI), Google Gemini, Groq, Hugging Face, and OpenAI.
Automatically falls back to local database knowledge engine on quota exhaustion or network timeouts.
"""

import os
import json
import logging
import requests
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

NEPAL_SYSTEM_PROMPT = """You are Himal AI, the intelligent, authoritative, and friendly Nepal Travel Companion.
You provide helpful, comprehensive, and accurate advice to travelers exploring Nepal across all 7 Provinces and 77 Districts.

Your core expertise:
1. Top Destinations: Kathmandu Valley (Pashupatinath, Boudhanath, Swayambhunath, Durbar Squares), Pokhara (Phewa Lake, Sarangkot, World Peace Pagoda), Annapurna Region (ABC, Poon Hill, Circuit, Tilicho), Everest Region (EBC, Namche Bazaar, Gokyo), Chitwan & Bardiya Wildlife Safaris, Lumbini (Birthplace of Lord Buddha), Rara Lake, Langtang Valley, Mustang/Muktinath, Bandipur, Ilam tea gardens, Janakpurdham.
2. Treks & Permits: TIMS card, ACAP, MCAP, Sagarmatha National Park entry, restricted area permits for Upper Mustang/Manaslu/Dolpo. Altitude sickness precautions (acclimatization days, hydration, Diamox, descending on AMS symptoms).
3. Travel Budgets: Backpacker ($20-$35/day or NPR 2,700-4,700), Mid-range ($45-$80/day or NPR 6,000-10,700), Luxury ($120+/day or NPR 16,000+). Local currency is Nepalese Rupee (NPR).
4. Distances & Routes: Provide realistic road distances and travel times (e.g. Kathmandu to Pokhara is 204 km via Prithvi Highway ~6-7 hrs drive or 25 min flight).
5. Safety & 24/7 Helplines:
   - Tourist Police: 1144 or +977-1-4247041
   - Nepal Police: 100
   - Ambulance: 102
   - Fire Service: 101
   - Traffic Police: 103
6. Seasons: Autumn (Sep-Nov: crystal clear peak views), Spring (Mar-May: rhododendrons in bloom), Monsoon (Jun-Aug: rain-shadow treks like Mustang/Dolpo), Winter (Dec-Feb: Terai wildlife and lower valley hikes).

Respond with structured markdown, bold headings, bullet points, and helpful travel tips."""


def ask_ai(message: str, context: str = "", history: list = None) -> str:
    """
    Tries configured AI providers in waterfall order:
    1. OpenRouter (Multi-model free/open access)
    2. Google Gemini
    3. Grok (xAI)
    4. Groq (Ultra-fast LLaMA)
    5. Hugging Face Inference
    6. OpenAI
    Returns response text or None if all providers fail/unconfigured.
    """
    # 1. Try OpenRouter
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        try:
            reply = call_openrouter(message, context, openrouter_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning("OpenRouter API error: %s", e)

    # 2. Try Gemini
    gemini_key = os.getenv("GEMINI_API_KEY")
    if gemini_key:
        try:
            reply = call_gemini(message, context, gemini_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning("Gemini API error: %s", e)

    # 3. Try Grok (xAI)
    grok_key = os.getenv("GROK_API_KEY") or os.getenv("XAI_API_KEY")
    if grok_key:
        try:
            reply = call_grok(message, context, grok_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning("Grok API error: %s", e)

    # 4. Try Groq
    groq_key = os.getenv("GROQ_API_KEY")
    if groq_key:
        try:
            reply = call_groq(message, context, groq_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning("Groq API error: %s", e)

    # 5. Try Hugging Face
    hf_key = os.getenv("HUGGINGFACE_API_KEY") or os.getenv("HF_TOKEN")
    if hf_key:
        try:
            reply = call_huggingface(message, context, hf_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning("Hugging Face API error: %s", e)

    # 6. Try OpenAI
    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        try:
            reply = call_openai(message, context, openai_key)
            if reply:
                return reply
        except Exception as e:
            logger.warning("OpenAI API error: %s", e)

    return None


def call_openrouter(message: str, context: str, api_key: str) -> str:
    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://digitalnepal.gov.np",
        "X-Title": "Digital Nepal Tourism",
    }
    user_prompt = f"Context:\n{context}\n\nQuestion: {message}" if context else message

    models_to_try = [
        "google/gemini-2.0-flash-exp:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "deepseek/deepseek-r1:free",
        "qwen/qwen-2.5-72b-instruct",
    ]

    for model in models_to_try:
        try:
            payload = {
                "model": model,
                "messages": [
                    {"role": "system", "content": NEPAL_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                "temperature": 0.6,
                "max_tokens": 1000,
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=12)
            if resp.status_code == 200:
                data = resp.json()
                choices = data.get("choices", [])
                if choices and "message" in choices[0]:
                    return choices[0]["message"]["content"].strip()
        except Exception:
            continue
    return None


def call_gemini(message: str, context: str, api_key: str) -> str:
    models = ["gemini-1.5-flash", "gemini-2.0-flash", "gemini-pro"]
    prompt_text = f"{NEPAL_SYSTEM_PROMPT}\n\nContext:\n{context}\n\nUser Question: {message}" if context else f"{NEPAL_SYSTEM_PROMPT}\n\nUser Question: {message}"
    headers = {"Content-Type": "application/json"}

    for model in models:
        try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt_text}]}],
                "generationConfig": {"temperature": 0.5, "maxOutputTokens": 1000}
            }
            resp = requests.post(url, headers=headers, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                candidates = data.get("candidates", [])
                if candidates and "content" in candidates[0]:
                    parts = candidates[0]["content"].get("parts", [])
                    if parts:
                        return parts[0].get("text", "").strip()
        except Exception:
            continue
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
        "max_tokens": 1000,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    return None


def call_groq(message: str, context: str, api_key: str) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    user_prompt = f"Context:\n{context}\n\nQuestion: {message}" if context else message
    payload = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": NEPAL_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.5,
        "max_tokens": 1000,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    return None


def call_huggingface(message: str, context: str, api_key: str) -> str:
    url = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.3"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    prompt_text = f"<s>[INST] {NEPAL_SYSTEM_PROMPT}\n\n{context}\n\n{message} [/INST]"
    payload = {
        "inputs": prompt_text,
        "parameters": {"max_new_tokens": 600, "temperature": 0.6, "return_full_text": False}
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
        "max_tokens": 1000,
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=10)
    if resp.status_code == 200:
        data = resp.json()
        return data["choices"][0]["message"]["content"].strip()
    return None
