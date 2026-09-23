"""
Free AI image generation via Pollinations.ai (Flux model).

Pollinations is a free, no-API-key AI image generator. We construct highly
specific prompts for each destination (name + district + region + visual
cues) so the output matches the actual place -- this is what prevents
"bike photo for Nagarkot" type mismatches.

We generate MULTIPLE variations per destination using different seeds and
camera styles (landscape, aerial, cultural, trekking) so each place gets
10-20 distinct, relevant images rather than one generic picture.

Because generation can be slow, the module only constructs URLs; the caller
downloads them (or stores them as external URLs) and validates them.
"""
from __future__ import annotations
import hashlib
from dataclasses import dataclass
from typing import List
from urllib.parse import quote


# Which Flux model to request.
MODEL = "flux"

# Variations to generate for each destination: (suffix added to prompt,
# width, height, style tag). Different angles make the gallery varied.
VARIATIONS = [
    ("wide landscape photograph, professional travel photography, golden hour", 1280, 720, "landscape"),
    ("aerial drone view, panoramic high-angle shot, daylight", 1280, 720, "aerial"),
    ("street-level documentary photograph, authentic local scene, natural light", 1024, 1024, "street"),
    ("architectural detail photograph, sharp focus, natural colours", 1024, 1024, "architectural"),
    ("cultural documentary photograph, people and traditions, candid", 1024, 1024, "cultural"),
    ("trekking / hiking landscape photograph, trail perspective, wide angle", 1280, 720, "trekking"),
    ("sunrise photograph, first light, warm golden tones, mist in valleys", 1280, 720, "sunrise"),
    ("sunset photograph, alpenglow on peaks, long shadows", 1280, 720, "sunset"),
    ("spring season, blooming rhododendron forests, clear sky", 1024, 1024, "spring"),
    ("autumn post-monsoon, crystal-clear Himalayan views, harvest light", 1024, 1024, "autumn"),
    ("close-up scenic photograph, foreground framing, depth of field", 1024, 1024, "closeup"),
    ("wide establishing shot, travel brochure quality, vibrant but natural", 1280, 720, "establishing"),
]

# Strong negative terms appended to every prompt to avoid wrong look.
NEGATIVE = ("blurry, low quality, distorted, text, watermark, logo, fake, "
            "European alps, Swiss chalet, Bhutanese dzong, Indian temple, "
            "Chinese pagoda, unrelated object, motorcycle, bike, car close-up, "
            "studio render, CGI, oversaturated")


@dataclass
class GeneratedImageSpec:
    url: str
    seed: int
    prompt: str
    style: str
    width: int
    height: int


def _region_cues(destination) -> str:
    """Build geographic/cultural description from real DB fields."""
    parts = []
    province = (getattr(destination, "province", "") or "").strip()
    district = (getattr(destination, "district", "") or "").strip()
    d_type = (getattr(destination, "type", "") or "").lower()
    cat = destination.category.name if getattr(destination, "category_id", None) else ""

    if province:
        parts.append(f"located in {province} province")
    if district:
        parts.append(f"{district} district")
    if "temple" in d_type or "temple" in (cat or "").lower() or "mandir" in destination.name.lower():
        parts.append("stone and wood tiered Hindu pagoda temple, carved struts, marigold offerings, bronze bells")
    elif "stupa" in d_type or "gompa" in d_type or "monastery" in d_type:
        parts.append("whitewashed Buddhist stupa with gilded spire, prayer flags, butter lamps")
    elif "lake" in destination.name.lower() or "pokhari" in destination.name.lower() or "tal" in destination.name.lower().split():
        parts.append("high-altitude freshwater lake reflecting snow peaks, wooden boats")
    elif "national park" in (cat or "").lower() or "chitwan" in destination.name.lower() or "bardiya" in destination.name.lower():
        parts.append("subtropical Terai sal forest and tall grassland, wildlife safari landscape")
    elif "hotel" in d_type or "guest" in d_type or "lodge" in d_type or "hostel" in d_type:
        parts.append("traveller accommodation building in a Nepali setting, mountain views")
    elif "hospital" in d_type or "hospital" in destination.name.lower():
        parts.append("local hospital / health-post building in a Nepali town")
    elif "viewpoint" in d_type or "view" in destination.name.lower():
        parts.append("scenic viewpoint overlooking Himalayan panorama")
    if not parts:
        parts.append("authentic Nepali landscape and architecture, terraced hills")
    return ", ".join(parts)


def build_prompt(destination, extra: str = "") -> str:
    """Construct a specific, grounded prompt for one destination."""
    name = destination.name
    cues = _region_cues(destination)
    desc = (getattr(destination, "description", "") or "")[:200]
    prompt = (
        f"A photorealistic travel photograph of {name}, Nepal. {cues}. "
        f"{desc} Geographically and culturally accurate to Nepal. "
        "Natural lighting, realistic textures, physically plausible geography, "
        "professional DSLR photograph, high detail. "
    )
    if extra:
        prompt += extra + ". "
    prompt += "Do not show unrelated objects, vehicles close-up, landmarks from other countries, text or watermarks."
    return " ".join(prompt.split())


def _seed_for(destination, style: str, salt: int = 0) -> int:
    raw = f"{destination.id or destination.name}-{style}-{salt}".encode()
    return int(hashlib.sha256(raw).hexdigest()[:8], 16) % 2_000_000_000


def generate_specs(destination, num: int = 12) -> List[GeneratedImageSpec]:
    """Return up to ``num`` image specs (URLs + prompts) for a destination."""
    specs = []
    for i, (suffix, w, h, style) in enumerate(VARIATIONS[:num]):
        prompt = build_prompt(destination, suffix)
        seed = _seed_for(destination, style, salt=i)
        encoded = quote(prompt[:1800], safe="")
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width={w}&height={h}&seed={seed}&model={MODEL}&nologo=true&enhance=true"
        )
        specs.append(GeneratedImageSpec(
            url=url, seed=seed, prompt=prompt, style=style, width=w, height=h,
        ))
    return specs
