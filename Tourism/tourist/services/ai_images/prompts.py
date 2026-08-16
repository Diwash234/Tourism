"""
Destination-specific prompt generation for AI image synthesis.

Builds a detailed, geographically/culturally grounded prompt from a
Destination's real metadata (type, region, elevation, cultural/geographic
characteristics) plus the requested variation (season, time of day, camera
style). This is what prevents "generic mountain" or wrong-country output.
"""
from __future__ import annotations
from dataclasses import dataclass

# Region-specific visual cues keyed by province/region. These are factual
# geographic / cultural descriptors, not invented landmarks.
REGION_CUES = {
    "koshi": "eastern Nepal hills, terraced farmland, Kanchenjunga and Kumbhakarna ranges, subtropical river valleys",
    "madhesh": "Terai plains, flat farmland, Mithila culture, colorful Janaki-style architecture, hot lowland light",
    "bagmati": "Kathmandu Valley, tiered Hindu pagoda temples, Buddhist stupas, brick Newari architecture, Himalayan backdrop",
    "gandaki": "Pokhara valley, Phewa Lake, Annapurna and Machhapuchhre Himalayan panorama, Gurung stone villages",
    "lumbini": "western Terai plains, Buddhist pilgrimage sites, Ashoka pillar, sal forest and monsoon greenery",
    "karnali": "remote far-western high Himalaya, trans-Himalayan dry valleys, Jumla and Rara Lake, alpine meadows",
    "sudurpashchim": "far-western hills and Terai, Khaptad plateau, Shuklaphanta grasslands, Seti river gorges",
}

# Destination-type cues.
TYPE_CUES = {
    "temple": "stone-and-wood tiered Hindu pagoda temple, carved struts, bronze bells, prayer bells, marigold offerings",
    "stupa": "whitewashed Buddhist stupa with gilded spire and all-seeing Buddha eyes, fluttering prayer flags, butter lamps",
    "monastery": "Tibetan Buddhist gompa with red walls, golden roof, prayer wheels, mani walls and stupas",
    "durbar square": "UNESCO Durbar Square with red-brick Newari palaces and carved wooden temples, stone pillars",
    "lake": "clear high-altitude freshwater lake mirroring snow peaks, wooden rowboats, reed-lined shore",
    "national park": "subtropical sal forest and tall grassland of Terai, wildlife safari landscape",
    "mountain": "high Himalayan peak with glaciers, moraine and snow ridges above cloud line",
    "trek": "stone trekking trail through rhododendron forest and terraced hills, Himalayan views",
    "hill station": "ridge-top hill town with panoramic Himalayan views, pine and rhododendron forest",
    "market": "traditional Nepali bazaar street with brick buildings, street vendors, rickshaws and temple spires",
    "waterfall": "steep waterfall through mossy subtropical gorge, monsoon-swollen white water",
}

NEGATIVE_PROMPT = (
    "European alps, Swiss chalets, Bhutanese dzong architecture, Tibetan plateau town outside Nepal, "
    "Indian Dravidian gopuram temple, Japanese pagoda, Chinese temple, skyscrapers, modern city skyline, "
    "snowy European village, desert, ocean beach, palm trees, fake landmarks, text, watermark, logo, "
    "blurry, low resolution, distorted faces, extra limbs, cartoon, 3d render, CGI, oversaturated, HDR, "
    "fictional architecture, misplaced Mount Everest"
)

SEASON_CUES = {
    "spring": "spring season, blooming red and pink rhododendron forests, clear mild light",
    "summer": "summer monsoon greenery, lush terraced fields, dramatic monsoon clouds, warm humid light",
    "autumn": "autumn post-monsoon crystal-clear sky, golden harvest light, crisp visibility of the Himalayas",
    "winter": "dry winter season, clear blue sky, snow-dusted peaks, warm low-angle sunlight",
}

TIME_CUES = {
    "sunrise": "golden hour sunrise, soft warm first light on peaks, long shadows, mist in the valleys",
    "day": "bright clear daytime, natural daylight, sharp detail, blue sky with light cloud",
    "sunset": "warm orange sunset, alpenglow on snow peaks, deepening blue sky, silhouetted ridges",
    "night": "blue hour twilight, village lights under a starry Himalayan sky, soft ambient light",
}

CAMERA_CUES = {
    "landscape": "wide-angle landscape photography, deep depth of field, natural colors",
    "aerial": "high aerial drone perspective, sweeping panoramic vista, top-down composition",
    "street": "street-level documentary photography, candid scene, 35mm lens",
    "architectural": "architectural photography, sharp detail of carvings and brickwork, natural light",
    "cultural": "cultural documentary photography, people in traditional Nepali dress, authentic scene",
    "trekking": "trekking landscape photography, trail winding through mountains, hiker for scale",
}


@dataclass
class PromptResult:
    prompt: str
    negative_prompt: str
    season: str
    time_of_day: str
    camera_style: str


def _region_key(text: str) -> str:
    t = (text or "").lower()
    for key in REGION_CUES:
        if key in t:
            return key
    return ""


def build_prompt(destination, season: str = "autumn", time_of_day: str = "day",
                 camera_style: str = "landscape", extra: str = "") -> PromptResult:
    """Compose a full photorealistic prompt from real destination fields."""
    name = destination.name or "a Nepali destination"
    d_type = (getattr(destination, "type", "") or "").lower()
    cat_name = destination.category.name if getattr(destination, "category_id", None) else ""
    region = _region_key(
        " ".join(filter(None, [
            getattr(destination, "province", ""),
            getattr(destination, "district", ""),
            getattr(destination, "region", ""),
            cat_name,
        ]))
    )
    elevation = getattr(destination, "altitude", "") or ""

    # Pick the best type cue
    type_cue = ""
    type_blob = " ".join([d_type, cat_name.lower(), name.lower()])
    for key, cue in TYPE_CUES.items():
        if key in type_blob:
            type_cue = cue
            break
    if not type_cue:
        type_cue = "Nepali landscape with authentic local architecture and geography"

    region_cue = REGION_CUES.get(region, "Himalayan nation of Nepal, authentic geography and culture")
    season_cue = SEASON_CUES.get(season, SEASON_CUES["autumn"])
    time_cue = TIME_CUES.get(time_of_day, TIME_CUES["day"])
    camera_cue = CAMERA_CUES.get(camera_style, CAMERA_CUES["landscape"])

    desc = (getattr(destination, "description", "") or "")[:240]
    cultural = (getattr(destination, "cultural_significance", "") or "")[:160]

    prompt = (
        f"Create a photorealistic travel photograph representing {name}, Nepal. "
        f"{type_cue}. Setting: {region_cue}. "
        f"{f'Elevation about {elevation}. ' if elevation else ''}"
        f"Geographic and cultural details: {desc} {cultural} "
        f"Season/time: {season_cue}; {time_cue}. "
        f"Camera: {camera_cue}. "
        f"{extra} "
        "The scene must be geographically and culturally consistent with Nepal, "
        "showing accurate Nepali architecture, vegetation, terrain and lighting. "
        "Do not introduce landmarks, architecture, clothing, vegetation, terrain or objects "
        "associated with other countries. It should look like a professionally captured real "
        "travel photograph with natural lighting, realistic textures, physically plausible "
        "geography, accurate scale, and natural colors."
    )
    return PromptResult(
        prompt=" ".join(prompt.split()),
        negative_prompt=NEGATIVE_PROMPT,
        season=season, time_of_day=time_of_day, camera_style=camera_style,
    )
