# Asset licensing audit

Audit date: 26 September 2026. This records what is known about the rights to
every image and font the site ships or displays, what was removed, and what the
owner still needs to confirm. Nothing here is legal advice.

## Summary

| Asset group | Count | Status |
|---|---|---|
| Destination photos in the database (`DestinationImage`) | 14,861 | Openly licensed (Wikimedia Commons / Openverse). **3,605 have no author credit recorded.** |
| Bundled destination photos (`public/images/destinations/`) | 42 folders | **No source recorded.** Owner must confirm rights. |
| Photos copied from commercial tour sites | 5 | **Removed** in this audit |
| Unused bundled images (avatars, hero, symbols) | 12 files | **Removed** in this audit (not referenced anywhere) |
| National symbol images (`src/components/dashboard/*.jfif`) | 8 | **No source recorded.** Owner must confirm or replace. |
| Category illustrations (`public/images/categories/*.svg`), icons, PWA icons | - | Made for this project |
| Fonts | 2 families | Self-hosted, SIL Open Font License 1.1 |

## Database photos

All 14,861 rows are `is_verified=True`, with sources Openverse (8,123) and
Wikimedia Commons (6,738). None are AI-generated or scraped from image search.

Licences recorded: "See Commons file page" 10,112; CC BY-SA 4.0 2,204;
CC BY-SA 3.0 1,543; CC BY 2.0 172; CC0 148; CC BY 3.0 109; CC BY-SA 2.0 88.

**Action needed:** CC BY and CC BY-SA require crediting the author. 3,605 rows
have an empty `attribution`. The gallery shows the source and licence where
recorded, but those rows show no author name. Either fill `attribution` from the
Commons/Openverse file page (the `source_url` is stored) or hide those photos
until it is filled. The "See Commons file page" rows should also have their
actual licence copied into `license_type`.

## Bundled destination photos

`frontend/Tourism/public/images/destinations/` holds 42 folders of JPEGs used as
fallbacks when a destination has no database photo (`LOCAL_NEPAL_PHOTOS` in
`src/utils/imageUtils.js`). The six default home-page hero slides also use
them (for example `everest/base-camp.jpg`), so they are among the most visible
images on the site. There is no record of where they came from.

**Action needed:** confirm each is owned or licensed, and add a
`SOURCES.csv` (file, author, licence, source URL). Replace any you cannot confirm
with a Commons photo, or delete it; the site already falls back to the category
illustration.

## Removed in this audit

`public/images/destinations/corrected-media-sources.csv` lists five photos that
were copied from commercial tour-operator sites (getyourguide.com,
himalayantrekkingpath.com, ruggedtrailsnepal.com, nepalhikingteam.com,
thelonerider.com) with the note "admin should confirm reuse rights". No licence
was found, so the files and the code that used them were removed. The
destinations fall back to the category illustration until a licensed photo is
added through the media library.

Also removed, because nothing referenced them and they had no source:
`public/images/avatars/user1-3.jpg` (photos of people), `public/images/hero/hero.jpg`,
and `public/images/symbols/*.jfif` (duplicates of the files below).

## National symbols

`src/components/dashboard/` contains eight `.jfif` images (flag, map, cow,
Danphe, rhododendron, emblem, Dhaka topi, stupa) used by `NationalSymbols.jsx`
and the footer. File names such as `images.jfif` and `flag,png.jfif` suggest
they were saved from a search engine.

**Action needed:** replace with files whose licence is known. Public-domain
versions of the flag and emblem exist on Wikimedia Commons
(`Flag_of_Nepal.svg`, `Emblem_of_Nepal.svg`); photos of the others can be taken
from Commons with attribution.

## Admin image tools (licensing risk)

The admin panel includes tools that could introduce unlicensed or synthetic
images if used:

- `services/image_search/search.py` scrapes DuckDuckGo image results.
- `services/image_generation/` and `generate_*_images` commands create
  AI-generated images (Pollinations).
- `src/utils/imageProviders.js` queries Unsplash, Pexels, Pixabay, Openverse and
  Wikimedia from the browser (admin only).

None of the published photos came from DuckDuckGo or AI generation. Before
publishing anything from these tools, record its licence and source, and label
AI-generated images as such.

## Fonts

Inter and Noto Sans Devanagari are installed from npm
(`@fontsource-variable/inter`, `@fontsource-variable/noto-sans-devanagari`),
both SIL Open Font License 1.1, and served from the site itself. Google Fonts is
no longer contacted. Six families that were downloaded but never used (Cinzel,
Outfit, Playfair Display, Plus Jakarta Sans, Ubuntu, and the unused Devanagari
link) were dropped.

## Maps

Map tiles come from OpenStreetMap (data under ODbL, attribution shown on the
map) and Esri World Imagery for the satellite layer (Esri terms apply; keep its
attribution visible).
