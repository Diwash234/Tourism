"""Find genuinely place-specific photos on Wikimedia Commons and propose them.

Why this is careful
-------------------
The dataset's problem is not missing images, it is *plausible wrong* ones. A
generic-but-recognisable photo of Pokhara is more damaging than no photo,
because a traveller cannot tell it is wrong. So the whole design is built around
one rule: **never accept an image that only matches the place's city.**

Concretely, a candidate is rejected unless the file's own title or description
names the place -- an alias, the municipality, the landmark. A hit for
"Pokhara" is refused for "Ghandruk" even though Ghandruk is in Pokhara district,
because that is precisely the substitution this command exists to undo. The same
rule applies to hotels, and hotels are stricter still: the match must name the
hotel, so a beautiful photo of a Chitwan safari can never become the cover of
"Barahi Jungle Lodge".

Wikimedia Commons is used because it is a documented public API and every file
carries its own licence and author, so the provenance recorded here is real and
the attribution obligation can actually be met. Anything not free to reuse is
rejected outright.

What it will not do
-------------------
* It does not approve anything. Every proposal is written as
  ``ImageStatus.PENDING`` with no quality or realism score, so a human decides.
  Inventing a score is how "verified" came to mean nothing.
* It does not replace an image that is already specific to its place. A photo
  reused by two places is left alone and reported; only images standing in for
  places they do not depict are eligible.
* It never guesses. No match means the row is reported unresolved and left
  exactly as it is -- an honestly missing image beats a confidently wrong one.
* It does not delete the previous URL; it is moved to the row's caption history
  via provenance fields, so the change is reversible.

Usage
-----
    python manage.py repair_real_place_images --kind destination --limit 20
    python manage.py repair_real_place_images --kind hotel --limit 20 --apply

Requires an identifying User-Agent (``WIKIMEDIA_USER_AGENT``) as Wikimedia
asks of every API client. Attribution is printed and stored per image.
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand
from django.utils import timezone

from tourist.console_safe import make_console_utf8, safe_text
from tourist.management.commands.audit_cross_place_images import normalise_image_url

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
COMMINS_POOL = 50  # above this, run your own Wikimedia infrastructure

# Licences that permit reuse with attribution. Anything else -- including
# "no known copyright", which is not a licence -- is refused outright.
REUSABLE_LICENCE_MARKERS = (
    "cc-by", "cc by", "cc-zero", "cc0", "public domain", "pd-", "attribution",
    "gfdl", "free art", "fal",
)
NON_REUSABLE_MARKERS = (
    "non-free", "nc-", "fair use", "copyright", "all rights reserved",
)

# Words that describe a place's *context* rather than the place itself. If these
# are the only match, the image is a context photo, not a photo of the place.
CONTEXT_ONLY_TERMS = {
    "nepal", "kathmandu", "pokhara", "bhaktapur", "patan", "lalitpur", "chitwan",
    "sagarmatha", "everest", "annapurna", "himalaya", "himalayan", "province",
    "district", "municipality", "rural", "urban", "city", "town", "village",
    "valley", "landscape", "scenery", "view", "sunset", "sunrise", "panorama",
}

_WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def words(text: str) -> set[str]:
    return {w.lower() for w in _WORD.findall(text or "")}


def cache_key(query: str) -> str:
    """Hash the query: place names contain spaces and colons, which are illegal
    in a memcached key."""
    digest = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()[:32]
    return f"commons:v1:{digest}"


def _user_agent() -> str:
    configured = str(getattr(settings, "WIKIMEDIA_USER_AGENT", "") or "").strip()
    if configured:
        return configured
    return ("NepalYatraImageRepair/1.0 "
            "(https://github.com/Diwash234/Tourism; set WIKIMEDIA_USER_AGENT to your contact)")


@dataclass
class Candidate:
    title: str
    page_url: str
    image_url: str
    licence: str = ""
    author: str = ""
    matched_terms: set = field(default_factory=set)

    @property
    def page_display(self) -> str:
        return self.title.replace("File:", "")


class CommonsSearch:
    """Thin, polite client for the Commons search API."""

    def __init__(self, *, min_interval: float = 0.2, timeout: float = 15.0,
                 use_cache: bool = True, session=None):
        self.min_interval = max(0.1, float(min_interval))
        self.timeout = timeout
        self.use_cache = use_cache
        self._last = None
        self.requests_made = 0
        self.session = session or requests

    def search(self, query: str, limit: int = 10) -> list[dict]:
        if not query.strip():
            return []
        if self.use_cache:
            cached = cache.get(cache_key(query))
            if cached is not None:
                return cached
        params = {
            "action": "query",
            "format": "json",
            "generator": "search",
            "gsrsearch": f"filetype:bitmap {query}",
            "gsrnamespace": "6",           # File:
            "gsrlimit": str(max(1, min(50, limit))),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata",
            "iiurlwidth": "1280",
        }
        if self._last is not None:
            elapsed = time.monotonic() - self._last
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
        self._last = time.monotonic()
        response = self.session.get(
            COMMONS_API, params=params,
            headers={"User-Agent": _user_agent(), "Accept": "application/json"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        self.requests_made += 1
        payload = response.json() or {}
        pages = (payload.get("query") or {}).get("pages") or {}
        rows = []
        for page in pages.values():
            info = (page.get("imageinfo") or [{}])[0]
            if not info.get("url"):
                continue
            meta = info.get("extmetadata") or {}
            rows.append({
                "title": page.get("title", ""),
                "page_url": info.get("descriptionurl", ""),
                "image_url": info.get("thumburl") or info.get("url", ""),
                "licence": str((meta.get("LicenseShortName") or {}).get("value", "")),
                "author": re.sub(r"<[^>]+>", "", str((meta.get("Artist") or {}).get("value", "")))[:150],
            })
        if self.use_cache:
            cache.set(cache_key(query), rows, 60 * 60 * 24 * 30)
        return rows


def licence_is_reusable(licence: str) -> bool:
    text = (licence or "").lower()
    if not text:
        return False          # an unknown licence is not a reusable licence
    if any(bad in text for bad in NON_REUSABLE_MARKERS):
        return False
    return any(good in text for good in REUSABLE_LICENCE_MARKERS)


def specificity(
    place_names: list[str],
    haystack: str,
    context_names: set[str],
) -> set[str]:
    """Return the place terms the candidate genuinely names.

    Empty means the match is context-only -- it describes the city or the
    region, not the place -- and must be refused. This is the single check that
    stops "a Pokhara photo because the place is in Pokhara".
    """
    hay = words(haystack)
    matched: set[str] = set()
    for name in place_names:
        name_words = words(name)
        if not name_words:
            continue
        # Every token of the name must appear, so "Phewa" does not match a file
        # merely containing the word "lake", and "Hotel" alone never matches.
        if name_words.issubset(hay):
            # A name made only of context words ("Lakeside Pokhara") needs at
            # least one distinguishing token beyond the context words.
            if name_words - context_names:
                matched |= name_words
    return matched


class Command(BaseCommand):
    help = "Propose real, place-specific photos from Wikimedia Commons."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true",
                            help="Persist proposals. Without this nothing is written.")
        parser.add_argument("--kind", choices=["destination", "hotel", "all"], default="all")
        parser.add_argument("--limit", type=int, default=20,
                            help="Maximum places to attempt in this run.")
        parser.add_argument("--images-per-place", type=int, default=4,
                            help="Maximum new images proposed per place.")
        parser.add_argument("--min-places", type=int, default=2,
                            help="Only replace images shared by at least this many places.")
        parser.add_argument("--include-unreused", action="store_true",
                            help="Also try places whose current image is not shared.")

        # --- offline triage: no network, no guessing. These use evidence
        # --- already stored on the row itself.
        parser.add_argument(
            "--reassign-by-caption", action="store_true",
            help="When a shared image's caption or alt text names one of the places "
                 "using it, keep it there and mark the other holders for review.",
        )
        parser.add_argument(
            "--quarantine-shared", type=int, default=0, metavar="N",
            help="Flag images shared by N or more places for human review so they stop "
                 "being served. 0 disables. Needs --apply to take effect.",
        )
        parser.add_argument(
            "--fix-multiple-covers", action="store_true",
            help="Leave exactly one cover per destination (the best evidenced one).",
        )
        parser.add_argument(
            "--triage-only", action="store_true",
            help="Run only the offline triage steps; do not contact Commons.",
        )

    def handle(self, *args, **options):
        make_console_utf8()
        apply_changes = options["apply"]

        self.stdout.write("Wikimedia Commons image repair")
        self.stdout.write(f"  mode: {'APPLY' if apply_changes else 'DRY RUN (nothing written)'}")
        self.stdout.write("")
        self.stdout.write("Rules in force:")
        self.stdout.write("  - a candidate must name the place, not just its city or district")
        self.stdout.write("  - hotels must match the hotel itself; a destination photo is never a hotel photo")
        self.stdout.write("  - an image already specific to its place is preserved, not replaced")
        self.stdout.write("  - licences that are not clearly reusable are refused")
        self.stdout.write("  - every proposal is written as 'needs review' with no score")
        self.stdout.write("  - no match means the place is left exactly as it is")
        self.stdout.write("")

        triage = {}
        if options["reassign_by_caption"] or options["fix_multiple_covers"] \
                or int(options["quarantine_shared"]) > 0:
            triage = self._triage(apply_changes, options)

        if options["triage_only"]:
            self._triage_summary(triage)
            return

        search = CommonsSearch()
        limit = int(options["limit"])
        report: dict[str, int] = {}
        for kind in (("destination", "hotel") if options["kind"] == "all" else (options["kind"],)):
            rows = (self._destination_targets(options) if kind == "destination"
                    else self._hotel_targets(options))
            if not rows:
                self.stdout.write(f"{kind}: nothing eligible.")
                continue
            self.stdout.write(f"{kind}: {len(rows)} place(s) eligible")
            stats = self._process(kind, rows, search, options)
            report[kind] = stats

        self.stdout.write("")
        self.stdout.write("SUMMARY")
        for kind, stats in report.items():
            self.stdout.write(
                f"  {kind:12} proposals: {stats['proposed']:4}  added: {stats['added']:4}  "
                f"unresolved: {stats['unresolved']:4}  preserved: {stats['preserved']:4}"
            )
        self._triage_summary(triage)
        self.stdout.write("")
        if not apply_changes:
            self.stdout.write("Dry run. Re-run with --apply to write. Nothing has changed.")
        self.stdout.write(
            "Proposals are 'needs review'. A human must approve them before they are "
            "shown as verified media; nothing here sets an approval or a score."
        )
        self.stdout.write(
            "Image content on Wikimedia is licensed by its uploader, not by us. "
            "Attribution is recorded per image and is required for reuse."
        )

    # -- offline triage --------------------------------------------------

    def _triage(self, apply_changes, options) -> dict:
        """Fix what can be established from evidence already on the row.

        This needs no network and guesses nothing. The strongest signal available
        is text a human or an importer already wrote on the row: the caption and
        alt text of a shared image frequently name the place the photo is
        actually of. Where exactly one holder is named, that holder keeps the
        image and the rest are marked for review. This is a claim the data
        already makes about itself, not an inference.
        """
        from tourist.models import Destination, DestinationImage

        stats = {"reassign_kept": 0, "reassign_flagged": 0, "reassign_ambiguous": 0,
                 "quarantined": 0, "covers_cleared": 0}
        threshold = int(options["quarantine_shared"])

        holders: dict[str, list] = {}
        for row in DestinationImage.objects.values(
            "id", "destination_id", "external_url", "image_path",
            "alt_text", "caption", "is_cover", "verification_status",
        ):
            key = normalise_image_url(row["external_url"]) or normalise_image_url(row["image_path"])
            if key:
                holders.setdefault(key, []).append(row)

        dest_cache: dict[int, str] = {}

        def dest_name(dest_id):
            if dest_id not in dest_cache:
                dest_cache[dest_id] = Destination.objects.filter(pk=dest_id)\
                    .values_list("name", flat=True).first() or ""
            return dest_cache[dest_id]

        for key, rows in holders.items():
            if len(rows) < 2:
                continue
            if options["reassign_by_caption"]:
                # Ask the question once per image, not once per row: across all
                # holders of this image, is exactly one place named by the
                # captions/alt text? If so that place is the real subject.
                # (Asking per row is quadratic and flags the same rows many
                # times over, which is how a 26k-row table reported a million
                # "changes".)
                named: dict[int, list] = {}
                for row in rows:
                    evidence = words(f"{row.get('caption') or ''} {row.get('alt_text') or ''}")
                    if not evidence:
                        continue
                    dest_id = row["destination_id"]
                    if words(dest_name(dest_id)) and words(dest_name(dest_id)).issubset(evidence):
                        named.setdefault(dest_id, []).append(row)
                if len(named) == 1:
                    owner_id = next(iter(named))
                    stats["reassign_kept"] += 1
                    for other in rows:
                        if other["destination_id"] == owner_id:
                            continue
                        stats["reassign_flagged"] += 1
                        if apply_changes:
                            DestinationImage.objects.filter(pk=other["id"]).update(
                                verification_status=DestinationImage.ImageStatus.REJECTED,
                                is_verified=False,
                                review_note=(
                                    f"Image shared by {len(rows)} places; its own "
                                    f"caption/alt text names '{dest_name(owner_id)}'. "
                                    "Held for human review by repair_real_place_images."
                                ),
                            )
                elif len(named) > 1:
                    stats["reassign_ambiguous"] += 1
            if threshold and len(rows) >= threshold:
                for row in rows:
                    stats["quarantined"] += 1
                    if apply_changes:
                        DestinationImage.objects.filter(pk=row["id"]).update(
                            verification_status=DestinationImage.ImageStatus.PENDING,
                            is_verified=False,
                            review_note=(
                                f"Image is shared by {len(rows)} different places, so it "
                                "cannot be a photograph of all of them. Held for human "
                                "review by repair_real_place_images."
                            ),
                        )

        if options["fix_multiple_covers"]:
            for dest_id in Destination.objects.filter(
                gallery__is_cover=True
            ).values_list("id", flat=True).distinct():
                covers = list(
                    DestinationImage.objects.filter(destination_id=dest_id, is_cover=True)
                    .order_by("-verification_status", "ordering", "id")
                )
                for extra in covers[1:]:
                    stats["covers_cleared"] += 1
                    if apply_changes:
                        DestinationImage.objects.filter(pk=extra.pk).update(is_cover=False)

        self.stdout.write("")
        self.stdout.write("Offline triage (evidence already on the row, no network):")
        verb = "cleared" if apply_changes else "would clear"
        flagv = "flagged for review" if apply_changes else "would flag for review"
        quarv = "flagged for review" if apply_changes else "would flag for review"
        self.stdout.write(f"  caption-based reassignment: {stats['reassign_flagged']} rows {flagv}")
        if stats["reassign_ambiguous"]:
            self.stdout.write(
                f"    (skipped {stats['reassign_ambiguous']} image(s) where more than one "
                "holder's caption names a place -- the evidence does not pick a winner)"
            )
        if threshold:
            self.stdout.write(
                f"  images shared by >={threshold} places: {stats['quarantined']} rows {quarv}"
            )
        if options["fix_multiple_covers"]:
            self.stdout.write(f"  duplicate covers: {stats['covers_cleared']} extra {verb}")
        return stats

    def _triage_summary(self, triage):
        if not triage:
            return
        total = (triage.get("reassign_flagged", 0) + triage.get("quarantined", 0)
                 + triage.get("covers_cleared", 0))
        if total:
            self.stdout.write("")
            self.stdout.write(
                f"  triage total: {total} row(s) affected. Rejected/pending images are "
                "hidden from public galleries by the media gate until a reviewer decides."
            )

    # -- selection -------------------------------------------------------

    def _reused_images(self, min_places: int) -> dict:
        """Map normalised image identity -> number of places currently using it."""
        from tourist.models import DestinationImage, Hotel

        counts: dict[str, set] = {}
        for row in DestinationImage.objects.values("destination_id", "external_url", "image_path"):
            key = normalise_image_url(row["external_url"]) or normalise_image_url(row["image_path"])
            if key:
                counts.setdefault(key, set()).add(f"d{row['destination_id']}")
        for row in Hotel.objects.values("id", "external_image_url", "cover_image"):
            key = normalise_image_url(row["external_image_url"]) or normalise_image_url(row["cover_image"])
            if key:
                counts.setdefault(key, set()).add(f"h{row['id']}")
        return {k: len(v) for k, v in counts.items()}

    def _destination_targets(self, options) -> list:
        from tourist.models import Destination

        reused = self._reused_images(int(options["min_places"]))
        if not options["include_unreused"]:
            queryset = Destination.objects.filter(
                is_active=True, status=Destination.SubmissionStatus.APPROVED
            )
        else:
            queryset = Destination.objects.filter(
                is_active=True, status=Destination.SubmissionStatus.APPROVED
            )
        targets = []
        for dest in queryset.only("id", "name", "district", "city", "city_english",
                                  "municipality", "aliases"):
            images = list(dest.gallery.values_list("external_url", "image_path"))
            keys = [normalise_image_url(a) or normalise_image_url(b) for a, b in images]
            keys = [k for k in keys if k]
            shared = [k for k in keys if reused.get(k, 0) >= int(options["min_places"])]
            if shared or not keys:
                targets.append((dest, shared, len(keys)))
        targets.sort(key=lambda t: -len(t[1]))
        return targets

    def _hotel_targets(self, options) -> list:
        from tourist.models import Hotel

        reused = self._reused_images(int(options["min_places"]))
        targets = []
        for hotel in Hotel.objects.filter(is_active=True).only(
            "id", "name", "address", "destination__name", "destination__district"
        ):
            key = (normalise_image_url(hotel.external_image_url)
                   or normalise_image_url(hotel.cover_image))
            if not key:
                continue
            if reused.get(key, 0) < int(options["min_places"]):
                continue
            targets.append((hotel, [key], 1))
        return targets

    # -- work ------------------------------------------------------------

    def _process(self, kind, rows, search, options) -> dict:
        from tourist.models import DestinationImage

        stats = {"proposed": 0, "added": 0, "unresolved": 0, "preserved": 0}
        context_names = set(CONTEXT_ONLY_TERMS)

        for place, shared_keys, image_count in rows[: int(options["limit"])]:
            label = safe_text(getattr(place, "name", "?"), 55)
            if kind == "destination":
                names = self._destination_names(place)
                context_names = self._destination_context(place)
            else:
                # A hotel is matched on its own name only. The district is
                # context and must never satisfy the match on its own.
                names = [place.name]
                context_names = self._destination_context(place.destination)

            if not names:
                stats["unresolved"] += 1
                self.stdout.write(f"  [unresolved] {label}: no usable name to search for")
                continue

            query = " ".join(names[:2])
            try:
                found = search.search(query, limit=15)
            except requests.RequestException as exc:
                self.stdout.write(self.style.WARNING(f"  Commons unavailable: {exc}"))
                break

            accepted: list[Candidate] = []
            refused = 0
            for row in found:
                if not licence_is_reusable(row.get("licence", "")):
                    refused += 1
                    continue
                haystack = f"{row.get('title','')} {row.get('page_url','')}"
                if not specificity(names, haystack, context_names):
                    refused += 1
                    continue
                accepted.append(Candidate(
                    title=row["title"], page_url=row.get("page_url", ""),
                    image_url=row.get("image_url", ""),
                    licence=row.get("licence", ""), author=row.get("author", ""),
                ))

            if not accepted:
                stats["unresolved"] += 1
                self.stdout.write(
                    f"  [unresolved] {label}: {len(found)} search hits, none named this "
                    f"place ({refused} refused as context-only or not freely reusable)"
                )
                continue

            want = max(1, int(options["images_per_place"]))
            chosen = accepted[:want]
            already = {normalise_image_url(a) or normalise_image_url(b)
                       for a, b in place.gallery.values_list("external_url", "image_path")} \
                if kind == "destination" else {
                    normalise_image_url(place.external_image_url),
                    normalise_image_url(place.cover_image),
                }
            added = 0
            for candidate in chosen:
                if normalise_image_url(candidate.image_url) in already:
                    continue
                stats["proposed"] += 1
                if options["apply"]:
                    if kind == "destination":
                        DestinationImage.objects.create(
                            destination=place,
                            external_url=candidate.image_url,
                            source=DestinationImage.Source.WIKIMEDIA,
                            source_url=candidate.page_url[:500],
                            source_platform="Wikimedia Commons",
                            photographer=candidate.author,
                            license_type=candidate.licence,
                            attribution=f"{candidate.author} / {candidate.licence}"[:255],
                            # The model defaults these to APPROVED/True. A photo
                            # this command found by name-matching has not been
                            # seen by a person, so it must not be published as
                            # verified media.
                            verification_status=DestinationImage.ImageStatus.PENDING,
                            is_verified=False,
                            alt_text=safe_text(place.name, 200),
                            caption="Proposed by repair_real_place_images; awaiting human review",
                        )
                    else:
                        place.external_image_url = candidate.image_url
                        place.source = place.Source.MANUAL
                        place.source_url = candidate.page_url[:600]
                        place.save(update_fields=["external_image_url", "source", "source_url"])
                added += 1

            stats["added"] += added
            if added:
                verb = "added" if options["apply"] else "would add"
                self.stdout.write(self.style.SUCCESS(
                    f"  [{verb}] {label}: {added} new image(s) from "
                    f"{candidate_author_summary(chosen)}"
                ))
            else:
                stats["preserved"] += 1
                self.stdout.write(f"  [preserved] {label}: place-specific images already present")

        self.stdout.write(f"  ({search.requests_made} Commons requests this run)")
        return stats

    def _destination_names(self, dest) -> list[str]:
        names = [dest.name]
        if dest.municipality:
            names.append(dest.municipality)
        aliases = dest.aliases
        if isinstance(aliases, list):
            names.extend(str(a) for a in aliases if a)
        elif isinstance(aliases, str) and aliases:
            names.extend(part.strip() for part in aliases.split(",") if part.strip())
        seen, out = set(), []
        for name in names:
            key = name.lower()
            if key and key not in seen:
                seen.add(key)
                out.append(name)
        return out

    def _destination_context(self, dest) -> set[str]:
        context = set(CONTEXT_ONLY_TERMS)
        for value in (dest.district, dest.city, dest.city_english, dest.province):
            if value:
                context |= words(str(value))
        return context


def candidate_author_summary(candidates: list[Candidate]) -> str:
    licences = sorted({c.licence for c in candidates if c.licence})
    return ", ".join(licences[:2]) or "Wikimedia Commons"
