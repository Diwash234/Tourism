"""
tourist/svg_postcards.py
========================

Deterministic SVG "postcard" generator for Nepal destinations.

Instead of hotlinking to ~200 generic Unsplash stock photos that repeat across
7,000+ destinations (causing "same mountains / same boy biking / same river"
complaints), we generate a UNIQUE, Nepal-themed SVG for every destination
based on its name + category. Each SVG features:

  * A category-appropriate silhouette (mountain peaks, pagoda, stupa,
    waterfall, cave, lake, village, forest, wildlife, cable car, etc.)
  * A deterministic Nepal-palette gradient (mountain-green, terracotta,
    Himalayan-gold, dawn-pink, snow-blue, forest-green, etc.)
  * The destination name typeset in a subtle location-name band
  * Optional district / category tag

These are fast (inline vector), always-available, and most importantly:
EVERY DESTINATION GETS A UNIQUE VISUAL — no more photo repetition.
"""

from __future__ import annotations

import hashlib
from urllib.parse import quote

# Nepal brand palette
DEEP_GREEN = "#1f6b4d"
TERRACOTTA = "#c2603a"
HIM_GOLD = "#b8862f"
OFF_WHITE = "#faf8f4"
CHARCOAL = "#2b2b2b"
SNOW_WHITE = "#f4f1ea"
SKY_BLUE = "#8bb5d6"
FOREST_GREEN = "#2d5a3d"
SUNSET_PINK = "#e8a09a"
DAWN_GOLD = "#f0c987"
RHODODENDRON = "#c8373d"
RICE_GREEN = "#5e8a4a"
LAKE_TEAL = "#3d7c8c"
STONE_GREY = "#8a8175"
MAROON = "#6b2028"

# 40+ deterministic gradient palettes keyed by a hash.
PALETTES = [
    # Dawn/sunrise
    (DAWN_GOLD, SUNSET_PINK, "#f7e5c4"),
    (HIM_GOLD, "#e29a52", "#f6d9a8"),
    (SUNSET_PINK, "#d97a68", "#f0c5b0"),
    # Mountain
    (SKY_BLUE, "#c4dcee", "#f0f4f7"),
    ("#a0c4d8", "#e8f0f5", "#ffffff"),
    (DEEP_GREEN, "#3a8866", "#89c4a3"),
    # Forest
    (FOREST_GREEN, RICE_GREEN, "#a8c890"),
    ("#3e6b47", "#6e9f5a", "#c8dba8"),
    # Lake / river
    (LAKE_TEAL, "#5fa3b3", "#b8d8de"),
    ("#457b90", "#7daebf", "#cfe3ea"),
    # Heritage / terracotta
    (TERRACOTTA, "#d9895f", "#f0c5a5"),
    (MAROON, "#983a3a", "#d8856c"),
    (TERRACOTTA, HIM_GOLD, "#f0d9b0"),
    # Rhododendron
    (RHODODENDRON, "#d96668", "#f2c0bd"),
    # Mist / high altitude
    (STONE_GREY, "#b0a89b", "#e5e0d5"),
    ("#9e9e9a", "#d3cfc5", "#efece4"),
    # Tea / agriculture
    (RICE_GREEN, "#7aa55d", "#c8dea8"),
    ("#4a7a3a", "#7ba85f", "#bdd6a0"),
    # Snow / winter
    ("#c8dae8", "#e8f0f7", "#ffffff"),
    ("#b8cee0", "#dbe7ef", "#fafcff"),
    # Temple / spiritual
    (HIM_GOLD, "#d4a457", "#f3e0b8"),
    (MAROON, "#8b3a3a", "#c88880"),
    # Night / starry
    ("#1e2d3a", "#3d5a6e", "#6e8ea3"),
    # Sunset golden hour
    ("#e8a440", "#f0c460", "#f9e5a8"),
    # Monsoon green
    ("#2f6f44", "#5e9c68", "#a4c8a0"),
    # River gorge
    ("#5a7a84", "#8aa8b0", "#c8d6da"),
    # Village
    (RICE_GREEN, TERRACOTTA, "#e8c898"),
    (TERRACOTTA, "#8a6a48", "#d0b890"),
    # Spring
    ("#e89bb0", "#c87a96", "#f0d0d6"),
    # Autumn
    ("#c87a3a", "#e09850", "#f0d0a0"),
]


# ---------------------------------------------------------------------------
# Category silhouette SVGs (viewBox 0 0 800 500). These are simple Nepal
# themed vector silhouettes drawn on top of the gradient background.
# Each function returns an inner SVG string (inside the 800x500 viewBox).
# ---------------------------------------------------------------------------

def _sil_mountains(hue: int) -> str:
    # Three ranges: distant (light), mid, foreground (dark)
    base = ["#5a7a8f", "#3d5a6f", "#2a3f50"]
    cols = [f"hsl({hue % 360}, 20%, {35 + i*12}%)" for i in range(3)]
    # Snow caps for front range
    return f"""
    <path d="M0,370 L80,280 L150,340 L230,220 L310,310 L400,180 L490,290 L570,240 L650,320 L730,260 L800,340 L800,500 L0,500 Z" fill="{cols[0]}" opacity="0.7"/>
    <path d="M0,420 L100,330 L180,380 L260,270 L360,360 L440,240 L540,340 L620,290 L720,370 L800,310 L800,500 L0,500 Z" fill="{cols[1]}" opacity="0.85"/>
    <path d="M0,460 L80,380 L140,430 L220,340 L310,410 L400,300 L490,400 L580,350 L680,420 L760,370 L800,400 L800,500 L0,500 Z" fill="{cols[2]}"/>
    <path d="M220,340 L260,270 L290,330 Z" fill="#ffffff" opacity="0.9"/>
    <path d="M400,300 L440,240 L480,320 Z" fill="#ffffff" opacity="0.9"/>
    <path d="M600,360 L620,290 L650,360 Z" fill="#ffffff" opacity="0.85"/>
    """


def _sil_lake(hue: int) -> str:
    return f"""
    <rect x="0" y="320" width="800" height="180" fill="url(#water)"/>
    <path d="M0,330 L80,280 L150,310 L230,240 L310,290 L400,210 L490,280 L570,230 L650,300 L730,260 L800,290 L800,330 Z" fill="hsl({hue%360},25%,38%)"/>
    <path d="M0,340 L120,300 L200,325 L280,270 L360,315 L440,250 L540,310 L620,275 L720,320 L800,300 L800,340 Z" fill="hsl({hue%360},22%,48%)" opacity="0.8"/>
    <path d="M100,360 Q110,365 120,360 M200,380 Q220,385 240,380 M350,370 Q370,375 390,370 M500,390 Q520,395 540,390 M640,365 Q660,370 680,365" stroke="#ffffff" stroke-width="1.2" opacity="0.3" fill="none"/>
    <ellipse cx="650" cy="430" rx="18" ry="6" fill="#ffffff" opacity="0.25"/>
    """


def _sil_temple(hue: int) -> str:
    return f"""
    <!-- Ground -->
    <rect x="0" y="400" width="800" height="100" fill="hsl({hue%360},18%,35%)"/>
    <!-- Three-tier pagoda -->
    <g transform="translate(400,150)">
      <rect x="-60" y="220" width="120" height="30" fill="#5a3a28"/>
      <polygon points="-90,220 90,220 70,180 -70,180" fill="#8b2626"/>
      <rect x="-45" y="140" width="90" height="40" fill="#5a3a28"/>
      <polygon points="-80,140 80,140 60,100 -60,100" fill="#a4322d"/>
      <rect x="-35" y="80" width="70" height="20" fill="#5a3a28"/>
      <polygon points="-60,80 60,80 0,20" fill="#c84038"/>
      <!-- Gajur (spire) -->
      <polygon points="-10,20 10,20 0,-10" fill="#d4a457"/>
      <circle cx="0" cy="-15" r="6" fill="#d4a457"/>
      <!-- Prayer flags pole -->
      <line x1="-200" y1="250" x2="-200" y2="50" stroke="#4a3020" stroke-width="3"/>
      <line x1="200" y1="250" x2="200" y2="70" stroke="#4a3020" stroke-width="3"/>
    </g>
    <!-- Flags -->
    <g opacity="0.85">
      <rect x="180" y="70" width="18" height="12" fill="#c84038"/><rect x="180" y="90" width="18" height="12" fill="#f0c940"/><rect x="180" y="110" width="18" height="12" fill="#ffffff"/><rect x="180" y="130" width="18" height="12" fill="#3a8866"/><rect x="180" y="150" width="18" height="12" fill="#3a6fa8"/>
    </g>
    """


def _sil_stupa(hue: int) -> str:
    return f"""
    <rect x="0" y="400" width="800" height="100" fill="hsl({hue%360},18%,40%)"/>
    <g transform="translate(400,400)">
      <!-- Mandala base -->
      <rect x="-150" y="-30" width="300" height="30" fill="#f0e6d0"/>
      <rect x="-120" y="-60" width="240" height="30" fill="#e8ddc4"/>
      <rect x="-95" y="-85" width="190" height="25" fill="#e0d3b6"/>
      <!-- Dome (anda) -->
      <ellipse cx="0" cy="-130" rx="110" ry="75" fill="#ffffff"/>
      <!-- Harmika -->
      <rect x="-40" y="-220" width="80" height="30" fill="#d4a457"/>
      <!-- Spire (13 rings) -->
      <polygon points="-20,-220 20,-220 12,-320 -12,-320" fill="#d4a457"/>
      <g stroke="#b8924a" stroke-width="1" fill="none">
        <line x1="-20" y1="-230" x2="20" y2="-230"/><line x1="-18" y1="-240" x2="18" y2="-240"/>
        <line x1="-17" y1="-250" x2="17" y2="-250"/><line x1="-16" y1="-260" x2="16" y2="-260"/>
        <line x1="-15" y1="-270" x2="15" y2="-270"/><line x1="-14" y1="-280" x2="14" y2="-280"/>
        <line x1="-13" y1="-290" x2="13" y2="-290"/><line x1="-12" y1="-300" x2="12" y2="-300"/>
      </g>
      <!-- Parasol + jewel -->
      <circle cx="0" cy="-325" r="10" fill="#c84038"/>
      <circle cx="0" cy="-340" r="5" fill="#d4a457"/>
      <!-- Buddha eyes -->
      <text x="-42" y="-145" font-size="22" fill="#2b2b2b" font-family="serif">◉</text>
      <text x="24" y="-145" font-size="22" fill="#2b2b2b" font-family="serif">◉</text>
      <!-- Prayer flags -->
      <line x1="-280" y1="0" x2="-80" y2="-200" stroke="#8a6030" stroke-width="1.5"/>
      <line x1="280" y1="0" x2="80" y2="-200" stroke="#8a6030" stroke-width="1.5"/>
    </g>
    """


def _sil_waterfall(hue: int) -> str:
    return f"""
    <!-- Cliffs -->
    <path d="M0,200 L200,180 L250,200 L300,160 L340,200 L800,190 L800,500 L0,500 Z" fill="hsl({hue%360},18%,32%)"/>
    <path d="M0,240 L180,220 L260,260 L320,220 L380,260 L460,230 L540,270 L620,240 L700,260 L800,230 L800,500 L0,500 Z" fill="hsl({hue%360},20%,42%)"/>
    <!-- Falls -->
    <rect x="340" y="200" width="45" height="220" fill="#e8f2f7" opacity="0.85"/>
    <rect x="348" y="210" width="6" height="200" fill="#ffffff" opacity="0.7"/>
    <rect x="360" y="215" width="5" height="195" fill="#ffffff" opacity="0.6"/>
    <rect x="370" y="218" width="5" height="192" fill="#ffffff" opacity="0.5"/>
    <!-- Pool -->
    <ellipse cx="362" cy="420" rx="120" ry="25" fill="#5fa3b3" opacity="0.8"/>
    <ellipse cx="362" cy="425" rx="90" ry="18" fill="#8dc5d2" opacity="0.6"/>
    <!-- Mist -->
    <ellipse cx="362" cy="410" rx="80" ry="15" fill="#ffffff" opacity="0.3"/>
    """


def _sil_cave(hue: int) -> str:
    return f"""
    <!-- Cliff -->
    <path d="M0,150 L200,180 L400,160 L600,190 L800,170 L800,500 L0,500 Z" fill="hsl({hue%360},12%,28%)"/>
    <path d="M0,250 L180,280 L380,260 L580,280 L780,260 L800,270 L800,500 L0,500 Z" fill="hsl({hue%360},14%,35%)"/>
    <!-- Cave arch -->
    <path d="M280,500 L280,320 Q280,240 400,230 Q520,240 520,320 L520,500 Z" fill="#1a1a22"/>
    <path d="M300,500 L300,330 Q300,270 400,260 Q500,270 500,330 L500,500 Z" fill="#2a2a38" opacity="0.8"/>
    <!-- Stalactites -->
    <polygon points="330,290 340,340 350,290" fill="#3a3038" opacity="0.6"/>
    <polygon points="380,280 392,350 404,280" fill="#3a3038" opacity="0.6"/>
    <polygon points="440,285 450,330 460,285" fill="#3a3038" opacity="0.6"/>
    <!-- Glow from inside -->
    <ellipse cx="400" cy="400" rx="80" ry="40" fill="#f0c940" opacity="0.15"/>
    """


def _sil_forest(hue: int) -> str:
    import random
    rng = random.Random(hue)
    trees = ""
    for i in range(25):
        x = 30 + (i * 32) + rng.randint(-10, 10)
        h = 120 + rng.randint(0, 80)
        w = 28 + rng.randint(0, 18)
        y = 450 - h
        trees += f'<rect x="{x+w//2-3}" y="{y+h-30}" width="6" height="30" fill="#3a2a1a"/>'
        trees += f'<polygon points="{x},{y+h-20} {x+w},{y+h-20} {x+w//2},{y}" fill="hsl({110 + rng.randint(-15,20)},35%,{28+rng.randint(0,12)}%)"/>'
        trees += f'<polygon points="{x+4},{y+h-50} {x+w-4},{y+h-50} {x+w//2},{y+20}" fill="hsl({110 + rng.randint(-15,20)},40%,{35+rng.randint(0,10)}%)"/>'
    return f"""
    <rect x="0" y="380" width="800" height="120" fill="hsl({hue%360},25%,22%)"/>
    <path d="M0,380 Q200,360 400,370 Q600,380 800,360 L800,420 L0,420 Z" fill="hsl({hue%360},25%,28%)"/>
    {trees}
    """


def _sil_wildlife(hue: int) -> str:
    # Grassland + one-horned rhino silhouette
    return f"""
    <rect x="0" y="380" width="800" height="120" fill="hsl({hue%360},28%,32%)"/>
    <!-- Grass -->
    <g stroke="#8ba865" stroke-width="1.5" opacity="0.7">
      <path d="M50,460 L48,400 M60,460 L62,395 M70,460 L68,405 M120,460 L118,398 M130,460 L132,390 M140,460 L138,402 M180,460 L178,408 M190,460 L192,396 M200,460 L198,400"/>
      <path d="M650,460 L648,400 M660,460 L662,395 M670,460 L668,405 M720,460 L718,398 M730,460 L732,390 M740,460 L738,402"/>
    </g>
    <!-- Distant sal forest -->
    <path d="M0,390 Q100,355 200,375 Q300,350 400,370 Q500,345 600,365 Q700,350 800,370 L800,400 L0,400 Z" fill="hsl({hue%360},28%,26%)"/>
    <!-- Rhino silhouette (one-horned) -->
    <g transform="translate(350,320)" fill="#2b2b2b">
      <ellipse cx="60" cy="50" rx="65" ry="35"/>
      <ellipse cx="110" cy="75" rx="25" ry="20"/>
      <!-- Head -->
      <path d="M115,65 Q140,40 135,30 Q128,25 118,40 Z"/>
      <!-- Horn -->
      <path d="M132,32 L140,15 L138,28 Z"/>
      <!-- Legs -->
      <rect x="20" y="75" width="10" height="35"/>
      <rect x="45" y="75" width="10" height="35"/>
      <rect x="75" y="75" width="10" height="35"/>
      <rect x="95" y="75" width="10" height="35"/>
      <!-- Ear -->
      <ellipse cx="118" cy="28" rx="4" ry="6"/>
    </g>
    """


def _sil_village(hue: int) -> str:
    return f"""
    <!-- Terraced hills -->
    <path d="M0,400 L800,320 L800,500 L0,500 Z" fill="hsl({hue%360},30%,35%)"/>
    <path d="M0,430 Q200,380 400,385 Q600,370 800,350 L800,430 L0,430 Z" fill="hsl({hue%360},28%,42%)"/>
    <path d="M0,460 Q200,420 400,425 Q600,405 800,395 L800,460 L0,460 Z" fill="hsl({hue%360},25%,48%)"/>
    <!-- Terrace lines -->
    <path d="M0,445 Q200,400 400,405 Q600,390 800,370" stroke="#8aa86a" stroke-width="1" fill="none" opacity="0.5"/>
    <path d="M0,480 Q200,440 400,445 Q600,425 800,410" stroke="#8aa86a" stroke-width="1" fill="none" opacity="0.5"/>
    <!-- Houses -->
    <g fill="#d4a457" stroke="#5a3a28" stroke-width="1.5">
      <rect x="150" y="355" width="40" height="35"/><polygon points="145,355 195,355 170,330" fill="#c2603a"/>
      <rect x="250" y="375" width="35" height="30"/><polygon points="246,375 289,375 267,353" fill="#c2603a"/>
      <rect x="380" y="345" width="45" height="38"/><polygon points="375,345 430,345 402,318" fill="#c2603a"/>
      <rect x="500" y="365" width="40" height="32"/><polygon points="496,365 544,365 520,340" fill="#c2603a"/>
      <rect x="620" y="350" width="38" height="35"/><polygon points="616,350 662,350 639,325" fill="#c2603a"/>
    </g>
    """


def _sil_city(hue: int) -> str:
    return f"""
    <rect x="0" y="380" width="800" height="120" fill="hsl({hue%360},18%,38%)"/>
    <!-- Skyline -->
    <g fill="#5a4a40">
      <rect x="40" y="280" width="50" height="100"/>
      <rect x="100" y="240" width="60" height="140"/>
      <rect x="170" y="300" width="45" height="80"/>
      <rect x="225" y="200" width="70" height="180"/>
      <rect x="305" y="260" width="55" height="120"/>
      <rect x="370" y="170" width="80" height="210"/>
      <rect x="460" y="240" width="60" height="140"/>
      <rect x="530" y="280" width="50" height="100"/>
      <rect x="590" y="220" width="75" height="160"/>
      <rect x="675" y="270" width="55" height="110"/>
      <rect x="740" y="300" width="45" height="80"/>
    </g>
    <!-- Windows -->
    <g fill="#f0c940" opacity="0.7">
      <rect x="50" y="295" width="8" height="8"/><rect x="68" y="295" width="8" height="8"/><rect x="50" y="315" width="8" height="8"/><rect x="68" y="315" width="8" height="8"/><rect x="50" y="335" width="8" height="8"/>
      <rect x="112" y="255" width="8" height="8"/><rect x="130" y="255" width="8" height="8"/><rect x="148" y="255" width="8" height="8"/><rect x="112" y="275" width="8" height="8"/><rect x="130" y="275" width="8" height="8"/>
      <rect x="240" y="215" width="8" height="8"/><rect x="258" y="215" width="8" height="8"/><rect x="276" y="215" width="8" height="8"/><rect x="240" y="235" width="8" height="8"/><rect x="258" y="235" width="8" height="8"/>
      <rect x="388" y="185" width="8" height="8"/><rect x="406" y="185" width="8" height="8"/><rect x="424" y="185" width="8" height="8"/><rect x="388" y="205" width="8" height="8"/><rect x="406" y="205" width="8" height="8"/>
      <rect x="608" y="235" width="8" height="8"/><rect x="626" y="235" width="8" height="8"/><rect x="644" y="235" width="8" height="8"/>
    </g>
    <!-- Temple spire in distance -->
    <polygon points="395,170 425,170 410,130" fill="#c84038"/>
    """


def _sil_valley(hue: int) -> str:
    return f"""
    <!-- Back range -->
    <path d="M0,250 L120,180 L250,230 L380,140 L500,210 L620,170 L740,220 L800,200 L800,340 L0,340 Z" fill="hsl({hue%360},20%,42%)" opacity="0.7"/>
    <!-- Mid hills -->
    <path d="M0,320 L100,260 L220,300 L340,240 L460,290 L580,250 L700,300 L800,270 L800,400 L0,400 Z" fill="hsl({hue%360},25%,38%)"/>
    <!-- Valley floor / river -->
    <path d="M0,400 Q200,380 400,400 Q600,420 800,395 L800,500 L0,500 Z" fill="hsl({hue%360},25%,48%)"/>
    <path d="M0,430 Q200,410 400,430 Q600,450 800,425 L800,460 Q600,475 400,455 Q200,445 0,460 Z" fill="hsl(200,25%,55%)" opacity="0.6"/>
    """


def _sil_river(hue: int) -> str:
    return f"""
    <path d="M0,300 L150,340 L280,310 L400,380 L550,330 L700,370 L800,350 L800,500 L0,500 Z" fill="hsl({hue%360},22%,42%)"/>
    <path d="M0,380 Q150,350 250,390 Q400,430 500,400 Q650,370 800,410 L800,500 L0,500 Z" fill="#457b90"/>
    <path d="M0,420 Q200,390 380,430 Q550,460 800,430 L800,470 Q600,490 400,465 Q200,450 0,470 Z" fill="#7daebf" opacity="0.7"/>
    <!-- Rapids/whitewater -->
    <ellipse cx="200" cy="410" rx="30" ry="5" fill="#ffffff" opacity="0.4"/>
    <ellipse cx="450" cy="445" rx="25" ry="4" fill="#ffffff" opacity="0.35"/>
    <ellipse cx="680" cy="420" rx="35" ry="5" fill="#ffffff" opacity="0.3"/>
    """


def _sil_trekking(hue: int) -> str:
    # Trail + hiker silhouette
    return _sil_mountains(hue) + f"""
    <!-- Trail -->
    <path d="M0,490 Q200,440 400,460 Q600,420 800,440" stroke="#c8a878" stroke-width="14" fill="none" opacity="0.5"/>
    <!-- Hiker silhouette -->
    <g transform="translate(380,395)" fill="#1a1a1a">
      <circle cx="0" cy="0" r="7"/>
      <rect x="-3" y="6" width="6" height="20"/>
      <rect x="-8" y="8" width="16" height="4"/>
      <rect x="-3" y="26" width="4" height="18" transform="rotate(-15 -1 35)"/>
      <rect x="0" y="26" width="4" height="18" transform="rotate(10 2 35)"/>
      <!-- Backpack -->
      <rect x="-9" y="8" width="7" height="15" rx="2"/>
      <!-- Trekking poles -->
      <line x1="-12" y1="20" x2="-18" y2="50" stroke="#1a1a1a" stroke-width="2"/>
      <line x1="9" y1="20" x2="15" y2="50" stroke="#1a1a1a" stroke-width="2"/>
    </g>
    """


def _sil_viewpoint(hue: int) -> str:
    return f"""
    {_sil_mountains(hue)}
    <!-- View tower / observation platform -->
    <g transform="translate(600,310)" fill="#5a3a28" stroke="#3a2a1a" stroke-width="1">
      <rect x="0" y="40" width="6" height="80"/><rect x="34" y="40" width="6" height="80"/>
      <rect x="-4" y="35" width="48" height="8"/>
      <polygon points="-8,35 52,35 22,10" fill="#c2603a"/>
      <!-- Railing -->
      <rect x="-4" y="28" width="48" height="3"/>
    </g>
    """


def _sil_heritage(hue: int) -> str:
    # Durbar square style palace
    return f"""
    <rect x="0" y="400" width="800" height="100" fill="hsl({hue%360},18%,35%)"/>
    <g fill="#8b4a2a" stroke="#5a2a1a" stroke-width="1">
      <rect x="100" y="280" width="600" height="120"/>
      <!-- Windows (traditional) -->
      <g fill="#3a1a0a">
        <rect x="130" y="300" width="25" height="30"/><rect x="170" y="300" width="25" height="30"/>
        <rect x="210" y="300" width="25" height="30"/><rect x="250" y="300" width="25" height="30"/>
        <rect x="290" y="300" width="25" height="30"/><rect x="330" y="300" width="25" height="30"/>
        <rect x="370" y="300" width="25" height="30"/><rect x="410" y="300" width="25" height="30"/>
        <rect x="450" y="300" width="25" height="30"/><rect x="490" y="300" width="25" height="30"/>
        <rect x="530" y="300" width="25" height="30"/><rect x="570" y="300" width="25" height="30"/>
        <rect x="610" y="300" width="25" height="30"/><rect x="650" y="300" width="25" height="30"/>
        <!-- Doors -->
        <rect x="370" y="350" width="60" height="50" fill="#5a2a1a"/>
      </g>
      <!-- Tiered roof -->
      <polygon points="80,280 720,280 660,230 140,230" fill="#a4322d"/>
      <polygon points="160,230 640,230 580,190 220,190" fill="#c84038"/>
      <polygon points="220,190 580,190 400,130" fill="#e05040"/>
    </g>
    """


def _sil_tea(hue: int) -> str:
    return f"""
    <!-- Rolling tea hills -->
    <path d="M0,320 Q150,270 300,290 Q450,250 600,280 Q750,260 800,275 L800,500 L0,500 Z" fill="hsl({hue%360},32%,28%)"/>
    <path d="M0,370 Q200,320 400,340 Q600,310 800,330 L800,500 L0,500 Z" fill="hsl({hue%360},35%,35%)"/>
    <path d="M0,420 Q200,380 400,395 Q600,365 800,390 L800,500 L0,500 Z" fill="hsl({hue%360},38%,42%)"/>
    <!-- Tea rows -->
    <g stroke="#4a7a3a" stroke-width="2" fill="none" opacity="0.7">
      <path d="M0,340 Q200,300 400,315 Q600,290 800,305"/>
      <path d="M0,355 Q200,315 400,330 Q600,305 800,320"/>
      <path d="M0,390 Q200,350 400,365 Q600,340 800,360"/>
      <path d="M0,405 Q200,365 400,380 Q600,355 800,375"/>
      <path d="M0,440 Q200,410 400,420 Q600,400 800,415"/>
      <path d="M0,455 Q200,425 400,435 Q600,415 800,430"/>
    </g>
    """


def _sil_adventure(hue: int) -> str:
    # Rock climbing / cliff
    return f"""
    <rect x="0" y="200" width="300" height="300" fill="hsl({hue%360},15%,38%)"/>
    <path d="M0,200 L80,180 L150,200 L230,170 L300,200 L300,500 L0,500 Z" fill="hsl({hue%360},12%,45%)"/>
    <!-- Rock details -->
    <path d="M40,280 L80,300 L50,320 Z" fill="hsl({hue%360},12%,32%)" opacity="0.5"/>
    <path d="M180,350 L220,370 L190,400 Z" fill="hsl({hue%360},12%,32%)" opacity="0.5"/>
    <!-- Right side sky / other cliff -->
    <rect x="300" y="0" width="500" height="500" fill="url(#skygrad)"/>
    <path d="M500,300 L600,250 L700,280 L800,240 L800,500 L500,500 Z" fill="hsl({hue%360},15%,40%)"/>
    <!-- Climber rope -->
    <line x1="200" y1="100" x2="230" y2="380" stroke="#c84038" stroke-width="2"/>
    <!-- Climber silhouette -->
    <g transform="translate(220,350)" fill="#1a1a1a">
      <circle cx="0" cy="0" r="6"/>
      <rect x="-2" y="5" width="4" height="15"/>
    </g>
    """


def _sil_watersports(hue: int) -> str:
    # Rafting
    return f"""
    {_sil_river(hue)}
    <!-- Raft -->
    <ellipse cx="400" cy="400" rx="55" ry="14" fill="#c84038"/>
    <!-- Paddles -->
    <line x1="350" y1="390" x2="320" y2="370" stroke="#3a2a1a" stroke-width="3"/>
    <line x1="450" y1="390" x2="480" y2="370" stroke="#3a2a1a" stroke-width="3"/>
    <line x1="360" y1="400" x2="340" y2="430" stroke="#3a2a1a" stroke-width="3"/>
    <line x1="440" y1="400" x2="460" y2="430" stroke="#3a2a1a" stroke-width="3"/>
    """


def _sil_cablecar(hue: int) -> str:
    return f"""
    {_sil_valley(hue)}
    <!-- Cable -->
    <line x1="0" y1="120" x2="800" y2="180" stroke="#3a3a3a" stroke-width="2"/>
    <line x1="0" y1="125" x2="800" y2="185" stroke="#5a5a5a" stroke-width="1"/>
    <!-- Support tower -->
    <rect x="200" y="130" width="6" height="200" fill="#5a5a5a"/>
    <polygon points="185,135 221,135 203,115" fill="#7a7a7a"/>
    <!-- Gondola -->
    <g transform="translate(450,145)">
      <rect x="-20" y="10" width="40" height="30" rx="4" fill="#c84038" stroke="#3a1a1a" stroke-width="1"/>
      <rect x="-16" y="14" width="14" height="12" fill="#b8d4e8"/><rect x="2" y="14" width="14" height="12" fill="#b8d4e8"/>
      <line x1="0" y1="10" x2="0" y2="-5" stroke="#3a3a3a" stroke-width="2"/>
      <circle cx="0" cy="-8" r="4" fill="#3a3a3a"/>
    </g>
    """


def _sil_winter(hue: int) -> str:
    # Snow scene
    return f"""
    <rect x="0" y="380" width="800" height="120" fill="#e8f0f7"/>
    <path d="M0,340 L120,260 L230,310 L340,220 L460,290 L580,240 L700,300 L800,270 L800,400 L0,400 Z" fill="#ffffff"/>
    <path d="M0,300 L100,230 L220,280 L340,200 L460,260 L580,210 L720,270 L800,240" stroke="#a8c0d0" stroke-width="1" fill="none"/>
    <!-- Snowflakes -->
    <g fill="#ffffff" opacity="0.8">
      <circle cx="100" cy="100" r="2"/><circle cx="250" cy="150" r="2"/><circle cx="400" cy="80" r="2"/>
      <circle cx="550" cy="130" r="2"/><circle cx="700" cy="90" r="2"/><circle cx="150" cy="200" r="2"/>
      <circle cx="320" cy="60" r="2"/><circle cx="620" cy="180" r="2"/><circle cx="480" cy="200" r="2"/>
    </g>
    """


def _sil_hotspring(hue: int) -> str:
    return f"""
    <!-- Rocky terrain -->
    <path d="M0,300 L200,320 L400,290 L600,330 L800,310 L800,500 L0,500 Z" fill="hsl({hue%360},12%,35%)"/>
    <!-- Pool -->
    <ellipse cx="400" cy="400" rx="180" ry="45" fill="#7daebf"/>
    <ellipse cx="400" cy="395" rx="150" ry="35" fill="#a8d0d8"/>
    <!-- Steam -->
    <g fill="#ffffff" opacity="0.35">
      <ellipse cx="350" cy="320" rx="40" ry="20"/><ellipse cx="420" cy="290" rx="35" ry="18"/>
      <ellipse cx="380" cy="260" rx="30" ry="15"/><ellipse cx="450" cy="310" rx="38" ry="20"/>
    </g>
    """


def _sil_museum(hue: int) -> str:
    return f"""
    <rect x="0" y="400" width="800" height="100" fill="hsl({hue%360},15%,38%)"/>
    <!-- Neoclassical museum -->
    <rect x="150" y="250" width="500" height="150" fill="#e0d8c8"/>
    <polygon points="130,250 670,250 400,180" fill="#c8b898"/>
    <!-- Columns -->
    <g fill="#f0e8d8" stroke="#b0a888" stroke-width="1">
      <rect x="200" y="260" width="20" height="130"/><rect x="260" y="260" width="20" height="130"/>
      <rect x="320" y="260" width="20" height="130"/><rect x="380" y="260" width="20" height="130"/>
      <rect x="440" y="260" width="20" height="130"/><rect x="500" y="260" width="20" height="130"/>
      <rect x="560" y="260" width="20" height="130"/>
    </g>
    <rect x="365" y="320" width="70" height="80" fill="#5a3a28"/>
    """


def _sil_food(hue: int) -> str:
    # Dal bhat / thali
    return f"""
    <rect x="0" y="350" width="800" height="150" fill="hsl({hue%360},25%,45%)"/>
    <!-- Table / tablecloth -->
    <ellipse cx="400" cy="400" rx="320" ry="80" fill="#c2603a"/>
    <!-- Thali (plate) -->
    <g transform="translate(400,380)">
      <ellipse cx="0" cy="0" rx="180" ry="50" fill="#d4a457"/>
      <ellipse cx="0" cy="0" rx="170" ry="45" fill="#e8c078"/>
      <!-- Rice mound -->
      <ellipse cx="0" cy="-5" rx="70" ry="22" fill="#ffffff"/>
      <!-- Dal bowl -->
      <ellipse cx="-100" cy="5" rx="35" ry="12" fill="#f0c940"/>
      <!-- Tarkari bowl -->
      <ellipse cx="80" cy="0" rx="30" ry="10" fill="#5e8a4a"/>
      <!-- Achar -->
      <ellipse cx="120" cy="10" rx="20" ry="8" fill="#c84038"/>
    </g>
    """


def _sil_festival(hue: int) -> str:
    return f"""
    <rect x="0" y="380" width="800" height="120" fill="hsl({hue%360},25%,40%)"/>
    <!-- Crowd silhouettes -->
    <g fill="#3a2a1a">
      <circle cx="100" cy="350" r="12"/><rect x="90" y="360" width="20" height="40"/>
      <circle cx="160" cy="345" r="12"/><rect x="150" y="355" width="20" height="45"/>
      <circle cx="220" cy="355" r="12"/><rect x="210" y="365" width="20" height="35"/>
      <circle cx="300" cy="340" r="12"/><rect x="290" y="350" width="20" height="50"/>
      <circle cx="400" cy="345" r="12"/><rect x="390" y="355" width="20" height="45"/>
      <circle cx="500" cy="350" r="12"/><rect x="490" y="360" width="20" height="40"/>
      <circle cx="580" cy="340" r="12"/><rect x="570" y="350" width="20" height="50"/>
      <circle cx="660" cy="355" r="12"/><rect x="650" y="365" width="20" height="35"/>
      <circle cx="720" cy="348" r="12"/><rect x="710" y="358" width="20" height="42"/>
    </g>
    <!-- Color powder in air (Holi) -->
    <g opacity="0.7">
      <circle cx="200" cy="200" r="30" fill="#c84038" opacity="0.3"/>
      <circle cx="400" cy="150" r="40" fill="#f0c940" opacity="0.25"/>
      <circle cx="600" cy="220" r="35" fill="#3a8866" opacity="0.25"/>
      <circle cx="300" cy="180" r="25" fill="#5fa3b3" opacity="0.3"/>
      <circle cx="500" cy="170" r="28" fill="#c84038" opacity="0.25"/>
    </g>
    """


def _sil_shopping(hue: int) -> str:
    return f"""
    <rect x="0" y="380" width="800" height="120" fill="hsl({hue%360},18%,38%)"/>
    <!-- Shop fronts -->
    <g>
      <rect x="50" y="230" width="130" height="150" fill="#c2603a"/>
      <rect x="190" y="210" width="150" height="170" fill="#b8862f"/>
      <rect x="350" y="220" width="140" height="160" fill="#1f6b4d"/>
      <rect x="500" y="240" width="130" height="140" fill="#6b2028"/>
      <rect x="640" y="220" width="140" height="160" fill="#c2603a"/>
    </g>
    <!-- Awnings -->
    <g>
      <polygon points="50,230 180,230 165,210 65,210" fill="#e8a040"/>
      <polygon points="190,210 340,210 320,190 210,190" fill="#c84038"/>
      <polygon points="350,220 490,220 470,200 370,200" fill="#f0c940"/>
      <polygon points="500,240 630,240 610,220 520,220" fill="#3a8866"/>
      <polygon points="640,220 780,220 760,200 660,200" fill="#e8a040"/>
    </g>
    """


def _sil_cycling(hue: int) -> str:
    # Scenic cycling path (NO person close-up, just scenic route)
    return f"""
    {_sil_hills_generic(hue)}
    <!-- Winding road -->
    <path d="M0,480 Q200,400 400,440 Q600,380 800,420" stroke="#8a7a60" stroke-width="20" fill="none"/>
    <path d="M0,480 Q200,400 400,440 Q600,380 800,420" stroke="#a89878" stroke-width="16" fill="none"/>
    """


def _sil_hills_generic(hue: int) -> str:
    return f"""
    <path d="M0,300 L150,240 L300,280 L450,210 L600,260 L750,220 L800,250 L800,500 L0,500 Z" fill="hsl({hue%360},28%,38%)"/>
    <path d="M0,360 Q200,310 400,340 Q600,300 800,330 L800,500 L0,500 Z" fill="hsl({hue%360},30%,45%)"/>
    <path d="M0,420 Q200,380 400,400 Q600,370 800,395 L800,500 L0,500 Z" fill="hsl({hue%360},32%,52%)"/>
    """


def _sil_camping(hue: int) -> str:
    return f"""
    {_sil_mountains(hue)}
    <!-- Tents -->
    <g>
      <polygon points="150,440 200,370 250,440" fill="#c84038"/>
      <polygon points="150,440 200,370 200,440" fill="#a03028"/>
      <polygon points="300,450 340,395 380,450" fill="#3a8866"/>
      <polygon points="430,445 470,380 510,445" fill="#f0c940"/>
      <polygon points="560,450 600,390 640,450" fill="#c84038"/>
    </g>
    <!-- Campfire -->
    <g transform="translate(250,430)">
      <ellipse cx="0" cy="20" rx="15" ry="4" fill="#3a2a1a"/>
      <path d="M-8,20 Q0,0 8,20 Q4,-5 0,-10 Q-4,-5 -8,20 Z" fill="#e87040"/>
      <path d="M-5,20 Q0,5 5,20 Q2,-3 0,-8 Q-2,-3 -5,20 Z" fill="#f0c940"/>
    </g>
    """


def _sil_general(hue: int) -> str:
    return _sil_mountains(hue)


def _sil_hotel(hue: int) -> str:
    return f"""
    <rect x="0" y="400" width="800" height="100" fill="hsl({hue%360},20%,40%)"/>
    <!-- Resort-style hotel with pool -->
    <rect x="150" y="250" width="500" height="150" fill="#f0e8d8"/>
    <!-- Roof -->
    <polygon points="140,250 660,250 600,210 200,210" fill="#c2603a"/>
    <!-- Windows -->
    <g fill="#b8d4e8" stroke="#8a8a8a" stroke-width="0.5">
      <rect x="180" y="280" width="25" height="25"/><rect x="220" y="280" width="25" height="25"/>
      <rect x="260" y="280" width="25" height="25"/><rect x="300" y="280" width="25" height="25"/>
      <rect x="340" y="280" width="25" height="25"/><rect x="380" y="280" width="25" height="25"/>
      <rect x="420" y="280" width="25" height="25"/><rect x="460" y="280" width="25" height="25"/>
      <rect x="500" y="280" width="25" height="25"/><rect x="540" y="280" width="25" height="25"/>
      <rect x="580" y="280" width="25" height="25"/>
      <rect x="180" y="325" width="25" height="25"/><rect x="220" y="325" width="25" height="25"/>
      <rect x="260" y="325" width="25" height="25"/><rect x="300" y="325" width="25" height="25"/>
      <rect x="340" y="325" width="25" height="25"/><rect x="380" y="325" width="25" height="25"/>
      <rect x="420" y="325" width="25" height="25"/><rect x="460" y="325" width="25" height="25"/>
      <rect x="500" y="325" width="25" height="25"/><rect x="540" y="325" width="25" height="25"/>
      <rect x="580" y="325" width="25" height="25"/>
      <!-- Door -->
      <rect x="370" y="365" width="60" height="35" fill="#5a3a28"/>
    </g>
    <!-- Pool -->
    <ellipse cx="400" cy="430" rx="250" ry="25" fill="#5fa3b3"/>
    <ellipse cx="400" cy="428" rx="230" ry="20" fill="#7dc0d0"/>
    """


def _sil_pilgrimage(hue: int) -> str:
    return _sil_temple(hue)


def _sil_spiritual(hue: int) -> str:
    # Combine stupa + prayer flags
    return f"""
    {_sil_stupa(hue)}
    <g opacity="0.6">
      <circle cx="150" cy="100" r="20" fill="#f0c940" opacity="0.3"/>
    </g>
    """


def _sil_park(hue: int) -> str:
    return f"""
    <rect x="0" y="380" width="800" height="120" fill="#6e9f5a"/>
    {_sil_forest(hue).replace('<rect x="0" y="380" width="800" height="120" fill="hsl({hue%360},25%,22%)"/>', '')}
    <!-- Path -->
    <path d="M380,500 Q400,450 420,420 Q430,400 400,380" stroke="#c8a878" stroke-width="12" fill="none" opacity="0.5"/>
    <!-- Bench -->
    <rect x="550" y="420" width="50" height="6" fill="#5a3a28"/>
    <rect x="555" y="426" width="4" height="18" fill="#5a3a28"/>
    <rect x="591" y="426" width="4" height="18" fill="#5a3a28"/>
    """


def _sil_bird(hue: int) -> str:
    return f"""
    <!-- Wetlands / Koshi Tappu style -->
    <rect x="0" y="350" width="800" height="150" fill="#6e9f5a"/>
    <ellipse cx="400" cy="400" rx="400" ry="40" fill="#7dc0d0" opacity="0.6"/>
    <!-- Reeds -->
    <g stroke="#5a7a3a" stroke-width="2">
      <line x1="100" y1="400" x2="95" y2="300"/><line x1="110" y1="400" x2="115" y2="290"/>
      <line x1="130" y1="400" x2="128" y2="310"/><line x1="700" y1="400" x2="695" y2="305"/>
      <line x1="710" y1="400" x2="715" y2="295"/><line x1="720" y1="400" x2="718" y2="315"/>
    </g>
    <!-- Birds in flight -->
    <g fill="none" stroke="#2b2b2b" stroke-width="2">
      <path d="M200,150 Q210,140 220,150 Q230,140 240,150"/>
      <path d="M300,120 Q310,110 320,120 Q330,110 340,120"/>
      <path d="M450,140 Q460,130 470,140 Q480,130 490,140"/>
      <path d="M550,100 Q560,90 570,100 Q580,90 590,100"/>
    </g>
    """


def _sil_airsports(hue: int) -> str:
    return f"""
    {_sil_valley(hue)}
    <!-- Paraglider wing -->
    <g transform="translate(400,200)">
      <path d="M-60,0 Q0,-40 60,0 Q40,-20 0,-25 Q-40,-20 -60,0 Z" fill="#c84038"/>
      <path d="M-30,-5 Q0,-35 30,-5" stroke="#f0c940" stroke-width="3" fill="none"/>
      <!-- Lines -->
      <line x1="-50" y1="0" x2="-5" y2="50" stroke="#3a3a3a" stroke-width="1"/>
      <line x1="50" y1="0" x2="5" y2="50" stroke="#3a3a3a" stroke-width="1"/>
      <line x1="0" y1="-20" x2="0" y2="50" stroke="#3a3a3a" stroke-width="1"/>
      <!-- Person -->
      <circle cx="0" cy="55" r="5" fill="#2b2b2b"/>
      <rect x="-4" y="60" width="8" height="15" fill="#2b2b2b"/>
    </g>
    """


def _sil_scenicroute(hue: int) -> str:
    return f"""
    {_sil_mountains(hue)}
    <!-- Winding highway -->
    <path d="M0,480 Q150,400 300,430 Q450,360 600,400 Q720,360 800,390" stroke="#5a5a5a" stroke-width="22" fill="none"/>
    <path d="M0,480 Q150,400 300,430 Q450,360 600,400 Q720,360 800,390" stroke="#7a7a7a" stroke-width="18" fill="none"/>
    <!-- Dashed center -->
    <path d="M0,480 Q150,400 300,430 Q450,360 600,400 Q720,360 800,390" stroke="#f0c940" stroke-width="2" stroke-dasharray="15,15" fill="none"/>
    """


def _sil_agriculture(hue: int) -> str:
    # Rice terraces
    return f"""
    <path d="M0,280 L800,200 L800,500 L0,500 Z" fill="hsl({hue%360},25%,30%)"/>
    <path d="M0,340 Q200,300 400,310 Q600,280 800,260 L800,370 Q600,390 400,370 Q200,390 0,370 Z" fill="hsl({hue%360},35%,40%)"/>
    <path d="M0,400 Q200,370 400,380 Q600,350 800,330 L800,430 Q600,450 400,430 Q200,450 0,430 Z" fill="hsl({hue%360},30%,48%)"/>
    <path d="M0,460 Q200,440 400,445 Q600,420 800,400 L800,500 L0,500 Z" fill="hsl({hue%360},28%,55%)"/>
    <!-- Water in terraces -->
    <path d="M0,350 Q200,310 400,320 Q600,290 800,270" stroke="#8cc0d0" stroke-width="3" fill="none" opacity="0.5"/>
    """


def _sil_eco(hue: int) -> str:
    return _sil_forest(hue)


def _sil_natural(hue: int) -> str:
    return _sil_mountains(hue)


def _sil_culture(hue: int) -> str:
    return _sil_festival(hue)


CATEGORY_SILHOUETTES = {
    "mountains": _sil_mountains,
    "mountain": _sil_mountains,
    "peaks": _sil_mountains,
    "hills": _sil_hills_generic,
    "hill-stations": _sil_hills_generic,
    "valleys": _sil_valley,
    "valley": _sil_valley,
    "lakes": _sil_lake,
    "lake": _sil_lake,
    "lakes-water-activities": _sil_lake,
    "rivers": _sil_river,
    "river": _sil_river,
    "waterfalls": _sil_waterfall,
    "waterfall": _sil_waterfall,
    "caves": _sil_cave,
    "cave": _sil_cave,
    "hot-springs": _sil_hotspring,
    "hot-spring": _sil_hotspring,
    "natural-wonders": _sil_natural,
    "viewpoints": _sil_viewpoint,
    "viewpoint": _sil_viewpoint,
    "view-tower": _sil_viewpoint,
    "forests": _sil_forest,
    "forest": _sil_forest,
    "wildlife": _sil_wildlife,
    "national-parks": _sil_wildlife,
    "national-park": _sil_wildlife,
    "bird-watching": _sil_bird,
    "birding": _sil_bird,
    "parks-gardens": _sil_park,
    "gardens": _sil_park,
    "parks": _sil_park,
    "park": _sil_park,
    "eco-tourism": _sil_eco,
    "agriculture": _sil_agriculture,
    "tea-coffee": _sil_tea,
    "tea-gardens": _sil_tea,
    "teagardens": _sil_tea,
    "temples": _sil_temple,
    "temple": _sil_temple,
    "hindu-temples": _sil_temple,
    "buddhist-sites": _sil_stupa,
    "buddhist": _sil_stupa,
    "stupas": _sil_stupa,
    "stupa": _sil_stupa,
    "monasteries": _sil_stupa,
    "monastery": _sil_stupa,
    "pilgrimage": _sil_pilgrimage,
    "spiritual-wellness": _sil_spiritual,
    "heritage": _sil_heritage,
    "heritage-temples": _sil_heritage,
    "unesco": _sil_heritage,
    "durbar-squares": _sil_heritage,
    "palaces": _sil_heritage,
    "museums": _sil_museum,
    "museum": _sil_museum,
    "culture": _sil_culture,
    "festivals": _sil_festival,
    "festival": _sil_festival,
    "cities": _sil_city,
    "city": _sil_city,
    "shopping": _sil_shopping,
    "food-culinary": _sil_food,
    "food": _sil_food,
    "villages": _sil_village,
    "village": _sil_village,
    "traditional-villages": _sil_village,
    "adventure": _sil_adventure,
    "climbing": _sil_adventure,
    "mountaineering": _sil_adventure,
    "trekking": _sil_trekking,
    "trek": _sil_trekking,
    "hiking": _sil_trekking,
    "air-sports": _sil_airsports,
    "paragliding": _sil_airsports,
    "bungee": _sil_adventure,
    "zip-flyer": _sil_airsports,
    "cablecar": _sil_cablecar,
    "cable-car": _sil_cablecar,
    "ropeway": _sil_cablecar,
    "water-sports": _sil_watersports,
    "rafting": _sil_watersports,
    "kayaking": _sil_watersports,
    "boating": _sil_watersports,
    "camping": _sil_camping,
    "cycling": _sil_cycling,
    "mountain-biking": _sil_cycling,
    "winter": _sil_winter,
    "snow": _sil_winter,
    "scenic-routes": _sil_scenicroute,
    "road-trips": _sil_scenicroute,
    "attraction": _sil_general,
    "attractions": _sil_general,
    "nature-trekking": _sil_trekking,
    "religious-sites": _sil_temple,
    "hotel": _sil_hotel,
    "resort": _sil_hotel,
    "guest_house": _sil_hotel,
    "hostel": _sil_hotel,
    "motel": _sil_hotel,
    "homestay": _sil_village,
    "general": _sil_general,
}


def generate_postcard_svg(
    name: str,
    category_slug: str = "general",
    district: str = "",
    width: int = 800,
    height: int = 500,
) -> str:
    """
    Generate a deterministic SVG postcard for a Nepal destination.

    Returns a complete SVG string (UTF-8) suitable for embedding or serving
    as an image response.
    """
    seed_str = f"{name.lower()}|{category_slug.lower()}|{district.lower()}"
    h = hashlib.md5(seed_str.encode("utf-8")).hexdigest()
    pal_idx = int(h[:4], 16) % len(PALETTES)
    hue = (int(h[4:8], 16) % 360)
    c1, c2, c3 = PALETTES[pal_idx]

    sil_fn = CATEGORY_SILHOUETTES.get(category_slug.lower().strip(), _sil_general)
    try:
        silhouette = sil_fn(hue)
    except Exception:
        silhouette = _sil_general(hue)

    # Name truncation for overlay band
    display_name = (name or "Nepal").strip()
    if len(display_name) > 42:
        display_name = display_name[:39] + "..."

    dist_line = ""
    if district:
        dist_line = f'<text x="40" y="62" font-family="sans-serif" font-size="16" fill="#faf8f4" opacity="0.85" letter-spacing="2" text-transform="uppercase">{_esc(district.upper())} • NEPAL</text>'

    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" preserveAspectRatio="xMidYMid slice">
  <defs>
    <linearGradient id="bggrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="55%" stop-color="{c2}"/>
      <stop offset="100%" stop-color="{c3}"/>
    </linearGradient>
    <linearGradient id="skygrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="60%" stop-color="{c2}"/>
      <stop offset="100%" stop-color="{c3}"/>
    </linearGradient>
    <linearGradient id="water" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="{LAKE_TEAL}" stop-opacity="0.85"/>
      <stop offset="100%" stop-color="#2a5a6a"/>
    </linearGradient>
    <filter id="soft" x="-10%" y="-10%" width="120%" height="120%">
      <feGaussianBlur stdDeviation="1"/>
    </filter>
  </defs>

  <!-- Background -->
  <rect width="{width}" height="{height}" fill="url(#bggrad)"/>

  <!-- Sun/moon disc -->
  <circle cx="{120 + (int(h[8:10],16) % 500)}" cy="{80 + (int(h[10:12],16) % 80)}" r="45" fill="#fff5e0" opacity="0.35"/>

  <!-- Clouds (subtle) -->
  <g fill="#ffffff" opacity="0.25">
    <ellipse cx="{200 + (int(h[12:14],16) % 400)}" cy="{100 + (int(h[14:16],16) % 50)}" rx="80" ry="14"/>
    <ellipse cx="{450 + (int(h[16:18],16) % 200)}" cy="{70 + (int(h[18:20],16) % 60)}" rx="60" ry="11"/>
  </g>

  <!-- Category silhouette -->
  <g>{silhouette}</g>

  <!-- Bottom name band -->
  <defs>
    <linearGradient id="band" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#000000" stop-opacity="0"/>
      <stop offset="50%" stop-color="#000000" stop-opacity="0.55"/>
      <stop offset="100%" stop-color="#000000" stop-opacity="0.8"/>
    </linearGradient>
  </defs>
  <rect x="0" y="370" width="{width}" height="130" fill="url(#band)"/>

  <!-- Nepal badge -->
  <g transform="translate(40,395)">
    <rect x="0" y="0" width="22" height="16" fill="#c8373d"/>
    <polygon points="22,0 44,8 22,16" fill="#ffffff"/>
    <polygon points="0,0 22,8 0,16" fill="#1f6b4d"/>
  </g>
  <text x="76" y="408" font-family="system-ui, sans-serif" font-size="13" font-weight="600" fill="#b8862f" letter-spacing="3">NEPAL TOURISM</text>
  {dist_line}
  <text x="40" y="460" font-family="system-ui, 'Segoe UI', sans-serif" font-size="28" font-weight="700" fill="#faf8f4">{_esc(display_name)}</text>
  <text x="40" y="483" font-family="system-ui, sans-serif" font-size="13" fill="#faf8f4" opacity="0.75" letter-spacing="1.5">Explore Nepal • {_esc(category_slug.replace('-', ' ').title())}</text>
</svg>
"""
    return svg


def _esc(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def postcard_url(name: str, category_slug: str = "general", district: str = "") -> str:
    """Return a URL that will serve this postcard SVG from Django."""
    from urllib.parse import quote
    cat = quote(category_slug or "general")
    nm = quote(name or "Nepal")
    dt = quote(district or "")
    return f"/api/v1/postcard/{cat}/{nm}/{dt}.svg"
