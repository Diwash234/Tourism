"""
Local Language & Dialect Model for Nepal (Nepali, Newari, Sherpa, Maithili)
"""

DICTIONARY = {
    "hello": {"ne": "नमस्ते (Namaste)", "new": "ज्वजलपा (Jwajalapa)", "sherpa": "ताशी देलेक (Tashi Delek)"},
    "thank you": {"ne": "धन्यवाद (Dhanyabad)", "new": "सुभाय् (Subhaye)", "sherpa": "थुजेछे (Thujechhe)"},
    "where is hospital": {"ne": "अस्पताल कहाँ छ? (Aspatal kaha chha?)", "sherpa": "मेन्खाङ खाबा यिन?"},
}

def translate_phrase(text: str, target_lang: str = "ne") -> str:
    cleaned = text.lower().strip()
    if cleaned in DICTIONARY:
        return DICTIONARY[cleaned].get(target_lang, DICTIONARY[cleaned]["ne"])
    return f"अनुवाद: {text} ({target_lang})"
