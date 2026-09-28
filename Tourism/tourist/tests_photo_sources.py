"""Reading candidate photographs out of Wikimedia Commons and Openverse.

The source adapters are where a wrong photograph gets in, so their rules are
pinned here. Two of them were learned the hard way.

*Openverse cannot do this job.* It allows 200 requests a day to an
unauthenticated caller, and the catalogue holds 6,514 destinations needing a
photograph -- 33 days of fetching. Commons publishes no daily cap and is where
19,331 of this library's existing photographs already come from, so it is the
default.

*A description is not evidence.* Matching a destination against a file's
description, as an earlier version did, offered "The Manaslu Hotel.jpg" for
"Shrestha Hotel" and "Namaste Jharna.jpg" for "Bhedetar Waterfall" -- both
because the description happened to mention the place somewhere. A Commons
description routinely names where the photographer stood and what the building
used to be. Only the file's own title says what the photograph shows.

No test here touches the network: the adapters take a payload and return
candidates, so the parsing and the refusals can be checked deterministically.
"""
from django.test import SimpleTestCase

from tourist.management.commands.fetch_destination_photos import (
    MIN_HEIGHT, MIN_WIDTH, PHOTO_MIMES, CommonsSource, OpenverseSource, readable,
    subject_of,
)
from tourist.photo_matching import match_score


def _page(title, mime="image/jpeg", width=2000, height=1500, **meta):
    """A Commons API page plus its imageinfo, shaped as the API returns it."""
    extmetadata = {
        "LicenseShortName": {"value": "CC BY-SA 4.0"},
        "LicenseUrl": {"value": "https://creativecommons.org/licenses/by-sa/4.0/"},
        "UsageTerms": {"value": "Creative Commons Attribution-Share Alike 4.0"},
        "ImageDescription": {"value": "A view from the south side."},
        "Artist": {"value": "Sabina Bajracharya"},
    }
    for key, value in meta.items():
        if value is None:
            extmetadata.pop(key, None)
        else:
            extmetadata[key] = {"value": value}
    return {
        "title": title,
        "imageinfo": [{
            "mime": mime,
            "width": width,
            "height": height,
            "url": f"https://upload.wikimedia.org/wikipedia/commons/a/ab/{title[5:]}",
            "thumburl": f"https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/"
                        f"{title[5:]}/1280px-{title[5:]}",
            "extmetadata": extmetadata,
        }],
    }


class ReadableTests(SimpleTestCase):
    def test_console_unsafe_characters_do_not_abort_a_run(self):
        # Many destinations are named in Devanagari. A command that dies with
        # UnicodeEncodeError partway through thousands of destinations has
        # wasted the whole run.
        text = readable("नमस्ते जमाल")
        self.assertIsInstance(text, str)
        self.assertTrue(text)

    def test_long_text_is_truncated_with_an_ellipsis(self):
        self.assertEqual(len(readable("x" * 200, 20)), 20)
        self.assertTrue(readable("y" * 200, 20).endswith("…"))


class CommonsQueryVariantTests(SimpleTestCase):
    class _Destination:
        name = "Davis Falls"
        district = "Kaski"

    def test_the_name_alone_is_tried_alongside_the_country(self):
        forms = CommonsSource.queries(self._Destination())
        self.assertIn("Davis Falls Nepal filetype:bitmap", forms)
        self.assertIn("Davis Falls filetype:bitmap", forms)

    def test_the_district_is_offered_when_known(self):
        forms = CommonsSource.queries(self._Destination())
        self.assertIn("Davis Falls Kaski filetype:bitmap", forms)

    def test_repeated_forms_are_not_requested_twice(self):
        class NoDistrict:
            name = "Pokhara"
            district = ""
        forms = CommonsSource.queries(NoDistrict())
        self.assertEqual(len(forms), len(set(forms)))

    def test_every_form_is_limited_to_bitmap_files(self):
        for form in CommonsSource.queries(self._Destination()):
            self.assertIn("filetype:bitmap", form)


class CommonsCandidateTests(SimpleTestCase):
    def setUp(self):
        self.source = CommonsSource()

    def test_a_properly_licensed_photograph_is_offered(self):
        page = _page("File:Davis Falls-Pokhara 03.jpg")
        candidate = self.source._to_candidate(page, page["imageinfo"][0])
        self.assertIsNotNone(candidate)
        self.assertEqual(candidate["license"], "CC BY-SA 4.0")
        self.assertEqual(candidate["creator"], "Sabina Bajracharya")
        self.assertIn("commons.wikimedia.org/wiki/", candidate["landing_url"])
        self.assertNotIn("?", candidate["url"], "a tracking query is not an image URL")

    def test_the_title_is_stripped_of_its_file_prefix(self):
        page = _page("File:Davis Falls-Pokhara 03.jpg")
        candidate = self.source._to_candidate(page, page["imageinfo"][0])
        self.assertEqual(candidate["title"], "Davis Falls-Pokhara 03.jpg")

    def test_only_the_title_is_matched_against(self):
        # The description says "A view from the south side", which names no
        # place. Matching on it is what produced the wrong photographs. The
        # caption keeps the description; the match text does not use it.
        page = _page("File:Davis Falls-Pokhara 03.jpg")
        candidate = self.source._to_candidate(page, page["imageinfo"][0])
        self.assertEqual(candidate["text"], "Davis Falls-Pokhara 03")
        self.assertEqual(candidate["description"], "A view from the south side.")
        self.assertEqual(match_score("Davis Falls", candidate["text"]), 1.0)
        self.assertEqual(match_score("Bhedetar Waterfall", candidate["text"]), 0.0)

    def test_a_file_with_no_licence_is_refused(self):
        page = _page("File:Some view.jpg", LicenseShortName=None)
        self.assertIsNone(self.source._to_candidate(page, page["imageinfo"][0]),
                          "reuse terms unknown means it may not be reused")

    def test_a_fair_use_file_is_refused(self):
        page = _page("File:Copyright logo.jpg", UsageTerms="Fair use")
        self.assertIsNone(self.source._to_candidate(page, page["imageinfo"][0]))

    def test_a_diagram_is_not_a_destination_photograph(self):
        for mime in ("image/svg+xml", "image/gif", "application/pdf"):
            page = _page("File:Map of the valley.svg", mime=mime)
            self.assertIsNone(self.source._to_candidate(page, page["imageinfo"][0]),
                              f"{mime} is not a photograph")
        self.assertNotIn("image/svg+xml", PHOTO_MIMES)

    def test_a_thumbnail_too_small_to_show_a_place_is_refused(self):
        page = _page("File:Tiny.jpg", width=MIN_WIDTH - 1, height=MIN_HEIGHT)
        self.assertIsNone(self.source._to_candidate(page, page["imageinfo"][0]))
        page = _page("File:Short.jpg", width=MIN_WIDTH, height=MIN_HEIGHT - 1)
        self.assertIsNone(self.source._to_candidate(page, page["imageinfo"][0]))

    def test_wiki_markup_in_the_author_is_stripped(self):
        page = _page("File:A.jpg",
                     Artist='<a href="//commons.wikimedia.org/wiki/User:X">X</a>')
        candidate = self.source._to_candidate(page, page["imageinfo"][0])
        self.assertEqual(candidate["creator"], "X")
        self.assertNotIn("<a", candidate["creator"])


class OpenverseCandidateTests(SimpleTestCase):
    ITEM = {
        "title": "Patan Durbar Square", "creator": "kkcondon",
        "license": "by-sa", "license_version": "2.0",
        "license_url": "https://creativecommons.org/licenses/by-sa/2.0/",
        "url": "https://example.test/patan.jpg?utm_source=x",
        "foreign_landing_url": "https://flickr.example/315373716",
        "tags": [{"name": "patan"}, {"name": "lalitpur"}],
    }

    def test_a_properly_licensed_result_is_offered(self):
        candidate = OpenverseSource._to_candidate(self.ITEM)
        self.assertEqual(candidate["license"], "BY-SA 2.0")
        self.assertEqual(candidate["creator"], "kkcondon")
        self.assertEqual(candidate["landing_url"], "https://flickr.example/315373716")

    def test_a_tracking_query_is_stripped_from_the_image_url(self):
        candidate = OpenverseSource._to_candidate(self.ITEM)
        self.assertEqual(candidate["url"], "https://example.test/patan.jpg")

    def test_matching_uses_title_and_tags_only(self):
        candidate = OpenverseSource._to_candidate(self.ITEM)
        self.assertEqual(match_score("Patan Durbar Square", candidate["text"]), 1.0)
        # The landing page and creator are not part of the evidence.
        self.assertNotIn("flickr", candidate["text"])
        self.assertNotIn("kkcondon", candidate["text"])

    def test_tags_arriving_as_plain_strings_are_also_handled(self):
        item = dict(self.ITEM, tags=["patan", "lalitpur"])
        candidate = OpenverseSource._to_candidate(item)
        self.assertEqual(match_score("Patan Durbar Square", candidate["text"]), 1.0)

    def test_a_result_with_no_licence_is_not_offered(self):
        for item in (dict(self.ITEM, license=""),
                     dict(self.ITEM, url=""),
                     dict(self.ITEM, license=None)):
            with self.subTest(item=item):
                self.assertIsNone(OpenverseSource._to_candidate(item))


class SubjectOfTests(SimpleTestCase):
    """The author's name is not what a photograph shows."""

    def test_an_author_clause_is_removed(self):
        # This is the real one: "Kailash Waterfall" was offered Dhuandhar
        # Waterfall in Madhya Pradesh, because the title ended
        # "... - panorama by Kailash Mohankar" and the author supplied the word
        # "Kailash".
        title = "File:Beautiful Dhuandhar Waterfall, Bhedaghat - panorama by Kailash Mohankar.jpg"
        self.assertNotIn("kailash", subject_of(title).lower())
        self.assertEqual(match_score("Kailash Waterfall", subject_of(title)), 0.0)

    def test_the_place_in_the_title_still_matches(self):
        self.assertEqual(
            match_score("Kailash Waterfall",
                        subject_of("File:Kailash Waterfall by Ram Bahadur.jpg")), 1.0)

    def test_a_trailing_file_id_is_removed(self):
        self.assertNotIn("26041822345", subject_of("File:Sunrise over Phewa (26041822345).jpg"))

    def test_a_title_with_neither_is_left_intact(self):
        self.assertEqual(
            subject_of("File:Phungphunge Waterfall.jpg"), "Phungphunge Waterfall")

    def test_nepali_names_that_are_also_photographers_are_not_matched_on(self):
        # Sagarmatha, Annapurna, Makalu and Gandaki are all mountains, rivers
        # and given names, so this collision is the rule rather than the
        # exception.
        title = "File:Annapurna from Poon Hill by Sagarmatha Rai.jpg"
        self.assertEqual(match_score("Annapurna Conservation Area", subject_of(title)), 0.0)


class RejectionIsThePointTests(SimpleTestCase):
    """The failures these rules prevent, stated as tests."""

    def test_a_photo_of_another_property_with_a_shared_word_is_rejected(self):
        # The exact wrong answer the description-matching version produced.
        self.assertEqual(
            match_score("Shrestha Hotel", "File:The Manaslu Hotel.jpg"), 0.0)
        self.assertEqual(
            match_score("Bhedetar Waterfall", "File:Namaste Jharna.jpg"), 0.0)

    def test_a_landscape_photograph_is_not_a_named_peak(self):
        self.assertEqual(
            match_score("Kanjirowa Himal", "File:View of Nepal - Himalayas.jpg"), 0.0)
