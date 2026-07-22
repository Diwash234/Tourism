"""
model/translation/translation_engine.py

Translates short phrases between Nepali and English for the tourism app
(menus, signs, emergency phrases, basic conversation).

For a real system you'd fine-tune or call a proper NMT model
(e.g. Helsinki-NLP/opus-mt-en-ne via transformers - see requirements.txt
comments). Until that's trained and saved under model/translation/model/,
this falls back to a small phrase dictionary loaded from
data/languages/ne-en.tsv so the API endpoint works end to end for the
common tourist/emergency phrases you'll want covered first.
"""
import os
import csv

PHRASES_PATH = os.path.join(
    os.path.dirname(__file__), "..", "..", "data", "languages", "ne-en.tsv"
)

_dictionary = None
_transformers_available = False

try:
    from transformers import pipeline  # noqa: F401
    _transformers_available = True
except ImportError:
    pass


def _load_dictionary() -> dict:
    global _dictionary
    if _dictionary is not None:
        return _dictionary

    _dictionary = {}
    if os.path.exists(PHRASES_PATH):
        with open(PHRASES_PATH, newline="", encoding="utf-8") as f:
            for row in csv.reader(f, delimiter="\t"):
                if len(row) >= 2:
                    ne, en = row[0].strip(), row[1].strip()
                    _dictionary[ne.lower()] = en
                    _dictionary[en.lower()] = ne
    return _dictionary


def translate(text: str, target_lang: str = "en") -> dict:
    if _transformers_available and os.path.exists(
        os.path.join(os.path.dirname(__file__), "model")
    ):
        # Hook for a real fine-tuned model once you've trained one.
        # translator = pipeline("translation", model=os.path.join(os.path.dirname(__file__), "model"))
        # result = translator(text)[0]["translation_text"]
        # return {"translation": result, "source": "model"}
        pass

    dictionary = _load_dictionary()
    match = dictionary.get(text.strip().lower())
    if match:
        return {"translation": match, "source": "dictionary"}

    return {
        "translation": None,
        "source": "unavailable",
        "message": "Phrase not found in dictionary and no trained model is loaded yet.",
    }