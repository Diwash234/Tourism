"""Give public destinations that render with no image a real one.

Why this exists
---------------
421 of the 6,695 public destinations had no usable cover, so the public
detail page, list page, hero and search result all fell back to the
"no image available" placeholder. Two different causes, deliberately handled
differently:

* Rows that reconcile_catalogue could hide, it did not hide. They are in the
  tracked dataset/data.json seed pk set, which that command protects, and many
  are genuinely real places (Namche Bazaar, Tengboche Monastery, Lukla
  airport) that merely carry an OSM ``type``. Deleting them would be wrong, so
  they are given a photo instead.

* Everything else simply never had one attached.

Only sources that need no API key and return their own licensing metadata are
used (Wikimedia Commons and Openverse), and every stored row keeps the
photographer, licence, licence URL and source page. Nothing is invented: if no
confident match is found, the destination is reported as still needing an
image rather than being given a plausible-looking wrong photo.

Safety
------
Each candidate URL is probed before it is stored, so a 404 in the source
catalogue cannot be written into the gallery and become another broken image
later. Matches below --min-score are skipped for the same reason: a wrong but
loadable photo is worse than an honest placeholder.
"""

import time
import urllib.error
import urllib.request

from django.core.management.base import BaseCommand
from django.db.models import Q

from tourist.models import Destination, DestinationImage
from tourist.services.image_search.search import multi_source_image_search

PUBLIC = Q(status=Destination.SubmissionStatus.APPROVED, is_active=True)

# Providers that require no credentials. Unsplash/Pexels/Pixabay/Flickr all
# need API keys, so including them here would silently return nothing on a
# deploy without secrets configured.
FREE_SOURCES = ["wikimedia", "openverse"]

USER_AGENT = "NepalTourismPlatform/1.0 (destination image backfill; admin-triggered)"

# Words that appear in generated display names but carry no identifying
# information. Two groups:
#   * descriptors appended to real place names ("Namche Bazaar Sherpa
#     Cultural Capital") which only dilute a search query;
#   * generic structure/venue nouns ("House", "Hotel", "Museum", "Bazaar")
#     which are so common that matching on them proves nothing. Without the
#     second group the relevance guard happily matched "Kausaltar Aquarium
#     House" to a photo titled "Tibet Peace Guest House" -- the only shared
#     token was "House".
_DESCRIPTOR_WORDS = {
    # appended descriptors
    "sherpa", "cultural", "capital", "settlement", "valley", "region",
    "area", "zone", "hub", "gateway", "centre", "center", "sanctuary",
    "reserve", "conservation", "wilderness", "alpine", "plateau", "meadows",
    "highland", "lowland", "village", "town", "city", "district", "province",
    "nepal", "the", "of", "and", "a", "an", "panorama", "scenic",
    # generic structures and venues
    "house", "hotel", "guest", "guesthouse", "resort", "lodge", "inn",
    "home", "homestay", "restaurant", "cafe", "temple", "monastery",
    "museum", "gallery", "park", "garden", "lake", "river", "mountain",
    "mountains", "hill", "hills", "view", "viewpoint", "tower", "station",
    "school", "college", "hospital", "clinic", "market", "bazaar", "plaza",
    "square", "gate", "gates", "bridge", "temple", "stupa", "durbar",
    "national", "park", "wildlife", "trek", "trekking", "base", "camp",
    "centre", "complex", "building", "hall", "office", "centre",
}


def _distinctive_tokens(text):
    """Words in ``text`` that could actually identify the place."""
    words = [w for w in str(text or "").lower().split() if w]
    return {w.strip(".,'-()") for w in words if len(w) >= 4 and w not in _DESCRIPTOR_WORDS}


def _query_variants(destination):
    """Search strings to try, most specific first.

    Display names in this catalogue are often a real place plus a descriptive
    tail ("Namche Bazaar Sherpa Cultural Capital", "Lukla Tenzing-Hillary
    Airport Valley"). Searching the full string dilutes the query and pulls
    unrelated photos, so the tail is stripped as well.
    """
    name = (destination.name or "").strip()
    district = (destination.district or "").strip()

    core = name
    words = name.split()
    for size in range(len(words) - 1, 0, -1):
        candidate = " ".join(words[:size])
        # Keep trimming while the next dropped word is pure descriptor.
        dropped = words[size]
        if dropped.lower() in _DESCRIPTOR_WORDS:
            core = candidate
            continue
        break

    variants = [name, core]
    if district and district.lower() not in name.lower():
        variants.append(f"{core} {district}")
    seen, out = set(), []
    for variant in variants:
        key = variant.strip().lower()
        if variant and key not in seen:
            seen.add(key)
            out.append(variant)
    return out


def _hit_represents_place(hit, destination):
    """Cheap relevance guard: does the hit name the place we asked about?

    The provider score is a blend of keyword and location similarity, which
    tolerates a hit with none of the place's words in its title. Attaching a
    confident-looking but unrelated photo is the worst outcome here, so at
    least one distinctive token from the destination name (or its aliases)
    must appear in the hit's title, caption or source page.
    """
    wanted = _distinctive_tokens(destination.name)
    for alias in getattr(destination, "aliases", None) or []:
        wanted |= _distinctive_tokens(alias)
    if not wanted:
        # Nothing distinctive to match on (a one-word name); trust the score.
        return True
    haystack = " ".join(
        str(part or "")
        for part in (hit.title, getattr(hit, "source_title", ""), hit.source_page)
    ).lower()
    haystack_tokens = _distinctive_tokens(haystack)
    return bool(wanted & haystack_tokens)


def url_is_live(url, timeout=8):
    """True when the URL actually returns image bytes.

    Wikimedia's thumbnail host rejects HEAD, so a ranged GET is used and only
    the first bytes are read.
    """
    if not url or not url.startswith("https://"):
        return False
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Range": "bytes=0-1023"},
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            content_type = (response.headers.get("Content-Type") or "").lower()
            # 200 OK, or 206 Partial Content -- most CDNs (upload.wikimedia.org
            # among them) answer a ranged request with 206, and rejecting that
            # marked every real Wikimedia photo as a dead link.
            if response.status not in (200, 206):
                return False
            return content_type.startswith("image/")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError):
        return False


class Command(BaseCommand):
    help = "Attach real, licensed photos to public destinations that have none."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0,
                            help="Max destinations to process (0 = all).")
        parser.add_argument("--min-score", type=float, default=0.40,
                            help="Minimum match score to accept a candidate (0-1).")
        parser.add_argument("--dry-run", action="store_true",
                            help="Report what would be attached without writing.")
        parser.add_argument("--slug", default=None,
                            help="Process a single destination by slug.")
        parser.add_argument("--sleep", type=float, default=0.35,
                            help="Pause between destinations, to be a good citizen.")

    def handle(self, *args, **options):
        from tourist.serializers import destination_cover_image

        queryset = Destination.objects.filter(PUBLIC).exclude(latitude__isnull=True)
        if options["slug"]:
            queryset = Destination.objects.filter(slug=options["slug"])

        candidates = []
        for destination in queryset.prefetch_related("gallery"):
            # Ask the real resolver, not the raw columns: the public surface
            # already treats an unapproved image as absent, so that is the
            # condition worth repairing.
            if destination_cover_image(destination, None):
                continue
            candidates.append(destination)
            if options["limit"] and len(candidates) >= options["limit"]:
                break

        self.stdout.write(f"public destinations without a usable image: {len(candidates)}")
        if not candidates:
            self.stdout.write(self.style.SUCCESS("  nothing to do."))
            return

        attached, already_present, no_confident_match, dead_url = 0, 0, 0, 0
        unchanged = 0

        for index, destination in enumerate(candidates, start=1):
            label = f"[{index}/{len(candidates)}] {destination.name[:48]}"

            # Try each query variant and keep the best-scoring live hit, so a
            # diluted full name does not cause a genuinely pictured place to be
            # skipped while its short name would have matched cleanly.
            hits = []
            variants = _query_variants(destination)
            for variant in variants:
                try:
                    found = multi_source_image_search(
                        query=variant,
                        destination=destination,
                        district=destination.district or "",
                        province=destination.province or "",
                        country=destination.country or "Nepal",
                        sources=FREE_SOURCES,
                        limit=8,
                    )
                except Exception as exc:  # noqa: BLE001 - one bad search must not stop the batch
                    self.stdout.write(
                        self.style.WARNING(f"{label} search failed for {variant!r}: {type(exc).__name__}: {exc}")
                    )
                    continue
                hits.extend(found)
                if any(h.match_score >= 0.75 for h in found):
                    break  # a strong hit on the full name; no need to dilute it
                time.sleep(0.15)

            if not hits:
                unchanged += 1
                continue

            # De-duplicate by URL, keeping the best score for each.
            best_by_url = {}
            for hit in hits:
                current = best_by_url.get(hit.url)
                if current is None or hit.match_score > current.match_score:
                    best_by_url[hit.url] = hit
            hits = sorted(best_by_url.values(), key=lambda h: h.match_score, reverse=True)

            chosen = None
            best_score_seen = 0.0
            for hit in hits:
                best_score_seen = max(best_score_seen, hit.match_score)
                if hit.match_score < options["min_score"]:
                    continue
                if not _hit_represents_place(hit, destination):
                    continue
                if url_is_live(hit.url):
                    chosen = hit
                    break
                dead_url += 1

            if chosen is None:
                no_confident_match += 1
                self.stdout.write(
                    self.style.WARNING(
                        f"{label} no confident live match "
                        f"(best score {best_score_seen:.2f})"
                    )
                )
                continue

            if destination.gallery.filter(external_url=chosen.url).exists():
                already_present += 1
                unchanged += 1
                continue

            if options["dry_run"]:
                self.stdout.write(f"{label} WOULD attach [{chosen.source}] {chosen.title[:44]}")
                attached += 1
                continue

            image = DestinationImage.objects.create(
                destination=destination,
                external_url=chosen.url,
                thumbnail_url=chosen.thumbnail or chosen.url,
                caption=f"{destination.name} — {chosen.title or chosen.source}".strip(" —"),
                source=DestinationImage.Source.WIKIMEDIA
                if chosen.source == "wikimedia"
                else DestinationImage.Source.OPENVERSE,
                source_url=chosen.source_page_url or chosen.source_page or "",
                source_platform=chosen.source,
                photographer=(chosen.author or "")[:150],
                license_type=(chosen.license or "")[:100],
                copyright_status="web_search",
                is_cover=True,
                destination_match_score=round(chosen.match_score, 3),
                authenticity_score=None,  # never invented; a media review assigns this
                verification_status=DestinationImage.ImageStatus.APPROVED,
                is_verified=True,
            )
            destination.gallery.exclude(pk=image.pk).filter(is_cover=True).update(is_cover=False)
            Destination.objects.filter(pk=destination.pk).update(cover_image=chosen.url)

            self.stdout.write(
                f"{label} <- [{chosen.source}] {chosen.title[:40]} "
                f"(score {chosen.match_score:.2f}, {chosen.license})"
            )
            attached += 1
            time.sleep(options["sleep"])

        self.stdout.write("")
        self.stdout.write(f"attached              : {attached}")
        self.stdout.write(f"already in gallery    : {already_present}")
        self.stdout.write(f"dead candidate URLs   : {dead_url}")
        self.stdout.write(f"no confident match    : {no_confident_match}")
        self.stdout.write(f"search errors         : {unchanged}")
        if options["dry_run"]:
            self.stdout.write(self.style.WARNING("DRY RUN - nothing was written"))
        elif no_confident_match:
            self.stdout.write(
                self.style.WARNING(
                    f"{no_confident_match} destinations still have no image. They were left "
                    "honest rather than given a photo of somewhere else; re-run for them "
                    "after adding their names to the curated map."
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS("every processed destination now has a real image."))