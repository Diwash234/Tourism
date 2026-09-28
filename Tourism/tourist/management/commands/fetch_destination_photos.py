"""Attach real, licensed photographs to destinations that lack their own.

Why this exists
---------------
An audit found 19,791 of the 20,168 real image rows were the *same photograph
reused across destinations*: one SAARC Secretariat picture on 331 places, a
Patan Durbar Square picture on 236. Only 377 rows were attached to exactly one
place. Those rows are worse than missing images, because they show a traveller a
confidently-labelled photograph of somewhere else.

`manage.py repair_misattributed_photos` removes that defect. This command fills
the gap it leaves, by acquiring a photograph *of the place being asked about*
and recording its creator, licence and landing page.

Why Wikimedia Commons
---------------------
Openverse, the obvious first choice, allows 200 requests a day to an
unauthenticated caller. At 6,612 destinations that is 33 days of fetching, so it
cannot do this job. Commons publishes no daily cap, is the home of the 19,331
Wikimedia photographs already in this library, and returns the licence,
author and description for every file. It is therefore the default source;
Openverse remains available with --source openverse, and --source both consults
the two in turn.

Safety rules, in order of importance
------------------------------------
1. Never attach a photograph whose own title or description does not name the
   place. A near-miss is left unattached rather than mis-attached.
2. Never attach a photograph already attached to a different destination --
   reusing one is precisely the defect being repaired.
3. Only freely-licensed files are used. A file with no licence, or one whose
   terms forbid reuse, is skipped. The licence name and URL are stored.
4. Nothing is invented. A destination with no evidence is reported and left
   without a photograph.
5. Dry run unless --apply is passed.

Usage
-----
    python manage.py fetch_destination_photos --report-only
    python manage.py fetch_destination_photos --limit 50
    python manage.py fetch_destination_photos --destination "Davis Falls"
    python manage.py fetch_destination_photos --apply
    python manage.py fetch_destination_photos --source both --apply
"""
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.html import strip_tags

from tourist.models import Destination, DestinationImage
from tourist.photo_matching import match_score

COMMONS = "https://commons.wikimedia.org/w/api.php"
OPENVERSE = "https://api.openverse.org/v1/images/"

#: Wikimedia asks callers to identify themselves and to keep request volume
#: reasonable. A tool that fetches thousands of files is exactly the case that
#: description exists for.
USER_AGENT = (
    "NepalYatraDataQA/1.0 (destination photograph accuracy repair; "
    "https://github.com/nepal-tourism; contact: repository maintainer)"
)

#: Only real raster photographs are usable as a destination photograph. SVG is
#: a diagram, a map or a logo; WEBP and GIF are not what a gallery shows.
PHOTO_MIMES = {"image/jpeg", "image/png"}
MIN_WIDTH = 640
MIN_HEIGHT = 400


def _clean(value):
    """Plain text from a field that may contain wiki markup or HTML."""
    if not value:
        return ""
    if isinstance(value, dict):
        value = value.get("value") or ""
    text = strip_tags(str(value))
    text = re.sub(r"\s+", " ", text).strip()
    return text


def readable(text, limit=60):
    """Text safe to print, whatever the console's encoding happens to be.

    Many destinations are named in Devanagari, and a management command that
    dies with UnicodeEncodeError partway through a run of several thousand
    destinations has wasted all of it. Characters the console cannot represent
    are shown as "?" rather than aborting the work.
    """
    text = str(text or "").strip()
    encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
    text = text.encode(encoding, errors="replace").decode(encoding, errors="replace")
    return text if len(text) <= limit else text[: limit - 1] + "…"


#: Commons titles routinely end in the photographer's name -- "Beautiful
#: Dhuandhar Waterfall, Bhedaghat - panorama by Kailash Mohankar.jpg". Matching
#: the whole title credits the destination with a match on the *author's* name,
#: and in Nepal that is a standing hazard rather than an unlucky one, because
#: names like Kailash, Sagarmatha, Annapurna, Gandaki and Makalu are also
#: mountains, rivers and towns. That is how "Kailash Waterfall" was offered a
#: photograph of Dhuandhar Waterfall in Madhya Pradesh.
_AUTHOR_CLAUSE = re.compile(r"\s+[-\u2013|]?\s*\bby\b\s+.*$", re.IGNORECASE)
#: A trailing Commons file id, as in "Sunrise over Phewa (26041822345).jpg".
_FILE_ID = re.compile(r"\s*\(\d{6,}\)")
_EXTENSION = re.compile(r"\.(jpg|jpeg|png|webp|gif|tiff?)$", re.IGNORECASE)
_FILE_PREFIX = re.compile(r"^\s*file\s*:\s*", re.IGNORECASE)


def subject_of(title):
    """The part of a file's name that says what the photograph shows.

    The ``File:`` prefix, the file extension, the trailing file id and the
    author's name are all removed, because none of them describes the subject
    and the last two carry words that collide with place names.
    """
    text = str(title or "").strip()
    text = _FILE_PREFIX.sub("", text)
    text = _EXTENSION.sub("", text)
    text = _FILE_ID.sub("", text)
    text = _AUTHOR_CLAUSE.sub("", text)
    return text.strip(" -_|,") or text


class CommonsSource:
    """Wikimedia Commons, which has no daily request cap."""

    name = "commons"

    #: Ways of asking. Commons full-text search rewards a plain place name, and
    #: appending "Nepal" to a name that already carries a district can push the
    #: real file out of the first page of results. The first query that yields a
    #: photograph naming the place wins, so trying more can only help recall --
    #: it cannot loosen the guard, which is applied to every candidate equally.
    @staticmethod
    def queries(destination):
        name = (destination.name or "").strip()
        district = (getattr(destination, "district", None) or "").strip()
        forms = [f"{name} Nepal", name]
        if district:
            forms.append(f"{name} {district}")
        seen, ordered = set(), []
        for form in forms:
            if form and form not in seen:
                seen.add(form)
                ordered.append(f"{form} filetype:bitmap")
        return ordered

    def search(self, destination, limit=12):
        found = []
        seen_urls = set()
        for term in self.queries(destination):
            for candidate in self._query(term, limit):
                if candidate["url"] not in seen_urls:
                    seen_urls.add(candidate["url"])
                    found.append(candidate)
            if found:
                break
        return found

    def _query(self, term, limit):
        query = {
            "action": "query",
            "format": "json",
            "formatversion": "2",
            "generator": "search",
            # Namespace 6 is File:, so only files come back, not articles.
            "gsrsearch": term,
            "gsrnamespace": "6",
            "gsrlimit": str(limit),
            "prop": "imageinfo",
            "iiprop": "url|extmetadata|size|mime",
            "iiurlwidth": "1280",
        }
        url = f"{COMMONS}?{urllib.parse.urlencode(query)}"
        request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, ValueError):
            return []
        pages = (payload.get("query") or {}).get("pages") or []
        results = []
        for page in pages:
            for info in page.get("imageinfo") or []:
                candidate = self._to_candidate(page, info)
                if candidate:
                    results.append(candidate)
        return results

    def _to_candidate(self, page, info):
        mime = (info.get("mime") or "").lower()
        if mime not in PHOTO_MIMES:
            return None
        if (info.get("width") or 0) < MIN_WIDTH or (info.get("height") or 0) < MIN_HEIGHT:
            return None
        meta = info.get("extmetadata") or {}
        licence_name = _clean(meta.get("LicenseShortName"))
        licence_url = _clean(meta.get("LicenseUrl"))
        if not licence_name:
            return None
        # A licence that permits no reuse cannot be republished.
        if _clean(meta.get("UsageTerms")).lower().find("fair use") >= 0:
            return None
        title = page.get("title") or ""
        description = _clean(meta.get("ImageDescription"))
        artist = _clean(meta.get("Artist"))
        file_url = info.get("url") or ""
        landing = "https://commons.wikimedia.org/wiki/" + urllib.parse.quote(
            title.replace(" ", "_"))
        return {
            "title": title.removeprefix("File:"),
            "description": description,
            # Matching deliberately uses the file's *name* and nothing else. A
            # Commons description routinely names half a dozen places -- where
            # the photographer stood, what the building used to be, a category
            # template -- and matching against it produced confident nonsense:
            # "Shrestha Hotel" was offered "The Manaslu Hotel.jpg" and
            # "Bhedetar Waterfall" was offered "Namaste Jharna.jpg", both
            # because their descriptions happened to mention the place. The
            # title is Commons' own name for what the photograph shows, so it
            # is the only text that can carry this weight. The description is
            # still stored, as a caption, but never used as evidence.
            "text": subject_of(title),
            "url": (info.get("thumburl") or file_url or "").split("?")[0],
            "original_url": (file_url or "").split("?")[0],
            "landing_url": landing,
            "creator": artist,
            "license": licence_name,
            "license_url": licence_url,
            "source": "wikimedia_commons",
        }


class OpenverseSource:
    """Openverse, kept because it indexes material Commons does not hold.

    Rate limited to 200 requests a day unauthenticated, so it cannot be the
    primary source for a whole catalogue.
    """

    name = "openverse"

    def search(self, destination, limit=12):
        query = urllib.parse.urlencode({
            "q": f"{destination.name} Nepal",
            "page_size": str(limit),
            "license_type": "all-cc,commercial",
        })
        request = urllib.request.Request(
            f"{OPENVERSE}?{query}", headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, ValueError):
            return []
        results = []
        for item in payload.get("results", []):
            candidate = self._to_candidate(item)
            if candidate:
                results.append(candidate)
        return results

    @staticmethod
    def _to_candidate(item):
        licence = (item.get("license") or "").lower()
        url = (item.get("url") or "").split("?")[0]
        # Reuse terms unknown means the result may not be reused.
        if not licence or not url:
            return None
        tags = item.get("tags") or []
        tag_text = " ".join(
            str(t.get("name") if isinstance(t, dict) else t) for t in tags)
        title = item.get("title") or ""
        creator = item.get("creator") or ""
        return {
            "title": title,
            "description": "",
            # Title and tags only, for the same reason as Commons: a tag is
            # chosen to name the subject, while free text and URLs are not
            # evidence of what a photograph shows.
            "text": " ".join([title, tag_text]),
            "url": url,
            "original_url": url,
            "landing_url": item.get("foreign_landing_url") or "",
            "creator": creator,
            "license": " ".join(filter(None, [
                licence.upper(), item.get("license_version") or ""])).strip(),
            "license_url": item.get("license_url") or "",
            "source": "openverse",
        }


SOURCES = {
    "commons": CommonsSource,
    "openverse": OpenverseSource,
}


class Command(BaseCommand):
    help = "Attach real, properly licensed photographs to destinations lacking their own."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=0,
                            help="Maximum destinations to attempt (0 = all).")
        parser.add_argument("--destination", default="",
                            help="Fetch for one destination by name.")
        parser.add_argument("--source", default="commons",
                            choices=["commons", "openverse", "both"],
                            help="Where to look (default: commons).")
        parser.add_argument("--report-only", action="store_true",
                            help="Report destinations lacking their own photo, fetch nothing.")
        parser.add_argument("--apply", action="store_true",
                            help="Write the photographs. Without this nothing changes.")
        parser.add_argument("--delay", type=float, default=0.2,
                            help="Seconds between API calls (default 0.2).")
        parser.add_argument("--include-covered", action="store_true",
                            help="Also revisit destinations that already have their own photo.")

    # -- helpers -----------------------------------------------------------
    def _shared_urls(self):
        """URLs currently attached to more than one destination."""
        from collections import defaultdict
        url_to_destinations = defaultdict(set)
        for url, destination_id in DestinationImage.objects.exclude(
                external_url="").values_list("external_url", "destination_id"):
            url_to_destinations[url].add(destination_id)
        return {url: ids for url, ids in url_to_destinations.items() if len(ids) > 1}

    def _uniquely_placed_ids(self):
        shared = self._shared_urls()
        shared_ids = set()
        for ids in shared.values():
            shared_ids |= ids
        return set(
            DestinationImage.objects.exclude(external_url="")
            .exclude(destination_id__in=shared_ids)
            .values_list("destination_id", flat=True)
        ), shared

    def _in_use(self):
        return set(DestinationImage.objects.exclude(
            external_url="").values_list("external_url", flat=True))

    def _best(self, destination, sources):
        for source in sources:
            best, best_score = None, 0.0
            for candidate in source.search(destination):
                score = match_score(destination.name, candidate["text"])
                if score > best_score:
                    best, best_score = candidate, score
            if best:
                return best, best_score, source.name
        return None, 0.0, None

    def _attach(self, destination, candidate, score):
        return DestinationImage.objects.create(
            destination=destination,
            external_url=candidate["url"],
            thumbnail_url=candidate["url"],
            caption=(candidate["title"] or destination.name)[:200],
            alt_text=(candidate["title"] or destination.name)[:255],
            attribution=(candidate["creator"][:250] or None),
            photographer=(candidate["creator"][:150] or None),
            license_type=candidate["license"][:100],
            copyright_status="verified_reusable",
            source_platform=candidate["source"],
            source_url=(candidate["landing_url"] or "")[:500] or None,
            verification_status=DestinationImage.ImageStatus.APPROVED,
            is_verified=True,
            is_cover=True,
            authenticity_score=1.0,
            destination_match_score=score,
        )

    # -- entry point -------------------------------------------------------
    def handle(self, *args, **options):
        destinations = Destination.objects.filter(
            is_active=True, status=Destination.SubmissionStatus.APPROVED
        ).order_by("id")

        uniquely_placed, shared = self._uniquely_placed_ids()
        if options["destination"]:
            destinations = destinations.filter(name__iexact=options["destination"])
        elif not options["include_covered"]:
            # Skip only destinations whose photograph is genuinely their own. A
            # destination holding a picture also attached to 300 other places
            # has no photograph, and is exactly the case this repairs, so
            # "has an image row" is the wrong test.
            destinations = destinations.exclude(id__in=uniquely_placed)

        total = destinations.count()
        self.stdout.write(f"destinations to consider: {total}")
        if shared:
            rows = sum(len(v) for v in shared.values())
            self.stdout.write(self.style.WARNING(
                f"note: {len(shared)} image URLs are attached to more than one "
                f"destination ({rows} rows). Run repair_misattributed_photos first; "
                f"those photographs will not be reused."))

        if options["report_only"]:
            self.stdout.write(f"destinations lacking their own photograph: {total}")
            return

        if not options["apply"]:
            self.stdout.write(self.style.WARNING(
                "DRY RUN - pass --apply to write. Nothing below is invented: each "
                "photograph is a freely-licensed file that names the place."))

        names = (["commons", "openverse"] if options["source"] == "both"
                 else [options["source"]])
        sources = [SOURCES[n]() for n in names]
        in_use = self._in_use()

        attached = 0
        refused_no_evidence = 0
        refused_in_use = 0
        errors = 0
        for destination in (destinations[: options["limit"]] if options["limit"]
                            else destinations):
            try:
                candidate, score, source_name = self._best(destination, sources)
            except Exception as exc:  # a flaky call must not end the run
                errors += 1
                self.stderr.write(
                    f"  {readable(destination.name)}: lookup failed ({exc})")
                continue
            if not candidate:
                refused_no_evidence += 1
                self.stdout.write(
                    f"  {readable(destination.name)}: no photograph names this place")
            elif candidate["url"] in in_use:
                refused_in_use += 1
                self.stdout.write(
                    f"  {readable(destination.name)}: only candidate is already used elsewhere")
            else:
                if options["apply"]:
                    with transaction.atomic():
                        self._attach(destination, candidate, score)
                in_use.add(candidate["url"])
                attached += 1
                if attached <= 40 or attached % 100 == 0:
                    self.stdout.write(self.style.SUCCESS(
                        f"  {readable(destination.name)}: "
                        f"\"{readable(candidate['title'], 44)}\" "
                        f"({candidate['license']}, {source_name})"))
            for source in sources:
                time.sleep(options["delay"])

        self.stdout.write("")
        self.stdout.write(f"attached or would attach        : {attached}")
        self.stdout.write(f"left without: no evidence      : {refused_no_evidence}")
        self.stdout.write(f"left without: only candidate in use: {refused_in_use}")
        if errors:
            self.stdout.write(f"lookup errors                 : {errors}")
        if not options["apply"]:
            self.stdout.write(self.style.WARNING("nothing was written; re-run with --apply"))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"attached {attached} real, licensed photographs"))
