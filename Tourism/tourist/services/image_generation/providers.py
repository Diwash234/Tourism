"""
Multiple free AI image-generation providers.

Each provider takes a SHORT prompt (under ~200 chars -- long prompts cause
providers like Pollinations to return colored error placeholders instead of
real images) and returns a direct image URL. The orchestrator tries them in
order until one returns a valid downloadable JPEG/PNG/WebP.

Providers are all FREE and require NO API key / billing:
  - Pollinations Flux
  - Pollinations Turbo
  - Pollinations with the 'realtime' model
  - Pollinations gptimage
  - Pollinations kling
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import quote


@dataclass
class ProviderSpec:
    name: str
    model: str
    base: str = "https://image.pollinations.ai/prompt/"
    extra: str = ""

    def url(self, prompt: str, seed: int, w: int = 1024, h: int = 768) -> str:
        p = quote(prompt[:220], safe="")
        u = f"{self.base}{p}?width={w}&height={h}&seed={seed}&model={self.model}&nologo=true&enhance=true"
        if self.extra:
            u += f"&{self.extra}"
        return u


# Multiple model variants so each image looks different, and if one model
# errors the orchestrator falls back to the next.
PROVIDERS: List[ProviderSpec] = [
    ProviderSpec("flux", "flux"),
    ProviderSpec("turbo", "turbo"),
    ProviderSpec("realtime", "realtimeImageGen"),
    ProviderSpec("gptimage", "gptimage"),
    ProviderSpec("kling", "kling"),
]


def make_short_prompt(destination, variation: str = "") -> str:
    """
    Build a SHORT, high-signal prompt (~15-25 words). Long prompts are what
    trigger the colored 'error' placeholder images. We keep the place name,
    Nepal, and one strong visual descriptor.
    """
    name = destination.name
    district = (getattr(destination, "district", "") or "").strip()
    d_type = (getattr(destination, "type", "") or "").lower()
    cat = destination.category.name if getattr(destination, "category_id", None) else ""
    blob = f"{d_type} {cat} {name}".lower()

    # Choose ONE strong visual descriptor based on type/category/name
    if any(w in blob for w in ("temple", "mandir", "pashupati", "nyatapola", "durbar")):
        scene = "ancient Hindu stone pagoda temple, carved wood, marigold offerings"
    elif any(w in blob for w in ("stupa", "gompa", "monastery", "boudha", "swayambhu")):
        scene = "white Buddhist stupa with golden spire and prayer flags"
    elif any(w in blob for w in ("lake", "pokhari", "phewa", "begnas", "rara", "tilicho")):
        scene = "clear mountain lake reflecting snow peaks, wooden boats"
    elif any(w in blob for w in ("national park", "chitwan", "bardiya", "koshi", "safari", "wildlife")):
        scene = "subtropical jungle and grassland, Terai Nepal, wildlife safari"
    elif any(w in blob for w in ("hotel", "guest house", "lodge", "resort", "hostel", "inn")):
        scene = "traveller lodge building with Himalayan mountain views"
    elif any(w in blob for w in ("hospital", "clinic", "health post", "swastha")):
        scene = "local health-post building in a Nepali hill town"
    elif any(w in blob for w in ("viewpoint", "view point", "sarangkot", "nagarkot")):
        scene = "panoramic Himalayan mountain viewpoint at sunrise"
    elif any(w in blob for w in ("mustang", "manang", "dolpa", "jumla", "humla")):
        scene = "dry trans-Himalayan high desert valley, eroded cliffs, Tibetan-style village"
    elif any(w in blob for w in ("trek", "trail", "trekking", "pass", "base camp", "himal", "peak", "mountain")):
        scene = "Himalayan trekking trail, snow peaks, rhododendron forest"
    elif any(w in blob for w in ("ilam", "tea", "kanyam")):
        scene = "rolling green tea gardens on misty eastern hills"
    elif any(w in blob for w in ("durbar square", "patan", "bhaktapur", "kirtipur", "bandipur")):
        scene = "traditional Newari brick palaces and carved wood temples"
    elif any(w in blob for w in ("lumbini", "mayadevi", "ashoka", "buddha birth")):
        scene = "Buddhist pilgrimage site with Ashoka pillar and sacred garden"
    elif any(w in blob for w in ("janakpur", "janaki", "mithila", "sitavividaha")):
        scene = "grand white marble Janaki Mandir temple with Mithila murals"
    elif any(w in blob for w in ("river", "khola", "gorge", "seti")):
        scene = "Himalayan river gorge, turquoise water, suspension bridge"
    elif any(w in blob for w in ("fall", "jharana", "waterfall", "davis")):
        scene = "steep waterfall in a green subtropical Nepali gorge"
    elif any(w in blob for w in ("bazaar", "market", "bazar", "chowk", "street")):
        scene = "traditional Nepali hill-town bazaar street, brick buildings"
    else:
        scene = "Nepali hill village with terraced fields and Himalayan backdrop"

    location = f"{name}, {district} district, Nepal" if district and district.lower() not in name.lower() else f"{name}, Nepal"
    prompt = f"photorealistic {scene}, {location}, professional travel photo, natural light, high detail{', ' + variation if variation else ''}"
    return " ".join(prompt.split())[:220]


# Camera/style variation suffixes - short, add visual variety
VARIATIONS = [
    "golden hour sunrise, wide angle",
    "aerial drone view",
    "blue hour, soft light",
    "sunset alpenglow on peaks",
    "clear autumn day, sharp detail",
    "misty morning, atmospheric",
    "street level documentary photo",
    "telephoto landscape, compressed peaks",
    "spring rhododendron bloom",
    "winter clear sky, snow peaks",
    "foreground framing, depth of field",
    "overcast soft light, moody",
]


def seed_for(destination, variation_idx: int) -> int:
    raw = f"{destination.id or destination.name}-v{variation_idx}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:8], 16) % 2_000_000_000


def build_candidates(destination, num: int = 12) -> list:
    """
    Return a list of (provider, url, prompt, seed, style) candidates to try,
    cycling through models and variations.
    """
    out = []
    for i in range(num):
        style = VARIATIONS[i % len(VARIATIONS)]
        prompt = make_short_prompt(destination, style.split(",")[0])
        seed = seed_for(destination, i)
        provider = PROVIDERS[i % len(PROVIDERS)]
        w, h = (1280, 720) if i % 3 == 0 else (1024, 1024) if i % 3 == 1 else (1024, 768)
        out.append({
            "provider": provider.name,
            "url": provider.url(prompt, seed, w, h),
            "prompt": prompt,
            "seed": seed,
            "style": style,
            "width": w, "height": h,
        })
    return out
