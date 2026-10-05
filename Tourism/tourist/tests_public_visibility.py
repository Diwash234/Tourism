"""Guards the optimised public-visibility filter.

`Destination.publicly_visible()` used to evaluate a REGEXP subquery on every
public query, which cost hundreds of milliseconds site-wide to hide two rows.
It now reads the indexed `is_unreadable_import` column, which `save()`
maintains. These tests pin the two properties that make that safe:

1. the cached flag selects exactly the rows the original regex selected, and
2. the flag cannot drift from the name, because save() recomputes it.
"""

from django.test import TestCase
from django.utils import timezone

from tourist.models import Destination


class UnreadableImportFlagTests(TestCase):
    """The cached flag must be equivalent to the regex it replaced."""

    def _dest(self, name, **kwargs):
        defaults = {
            "slug": name.lower().replace(" ", "-")[:40],
            "district": "Kathmandu",
            "province": "Bagmati",
        }
        defaults.update(kwargs)
        return Destination.objects.create(name=name, **defaults)

    def test_pure_cjk_name_is_flagged(self):
        row = self._dest("兰巴拉")  # CJK only
        self.assertTrue(row.is_unreadable_import)

    def test_pure_hangul_name_is_flagged(self):
        row = self._dest("더 노스 페이스 인")  # Hangul only
        self.assertTrue(row.is_unreadable_import)

    def test_cjk_with_latin_is_kept(self):
        """'Makalu' written with a CJK gloss is a real place, not junk."""
        row = self._dest("मकालु 马卡鲁峰")
        self.assertFalse(row.is_unreadable_import)

    def test_cjk_with_devanagari_is_kept(self):
        row = self._dest("बाँडुर्धन 马卡鲁")
        self.assertFalse(row.is_unreadable_import)

    def test_plain_romanised_name_is_kept(self):
        row = self._dest("Pokhara")
        self.assertFalse(row.is_unreadable_import)

    def test_empty_name_is_kept(self):
        row = self._dest("")
        self.assertFalse(row.is_unreadable_import)

    def test_helper_agrees_with_the_regex_it_caches(self):
        names = [
            "兰巴拉",
            "더 노스 페이스 인",
            "मकालु 马卡鲁峰",
            "Pokhara",
            "",
            " Kathmandu Durbar ",
            "日本語のホテル",
            "होटल मेरु",
        ]
        for name in names:
            with self.subTest(name=name):
                expected = bool(
                    Destination._UNREADABLE_NAME_RE.search(name or "")
                    and not Destination._READABLE_NAME_RE.search(name or "")
                )
                self.assertEqual(
                    Destination.is_unreadable_import_name(name), expected
                )

    def test_save_recomputes_the_flag_when_the_name_changes(self):
        """The flag must not be able to drift from the name it describes."""
        row = self._dest("Pokhara")
        self.assertFalse(row.is_unreadable_import)

        row.name = "兰巴拉"
        row.save()
        row.refresh_from_db()
        self.assertTrue(
            row.is_unreadable_import,
            "renaming to unreadable import garbage must re-flag the row",
        )

        row.name = "Pokhara Durbar Square"
        row.save()
        row.refresh_from_db()
        self.assertFalse(
            row.is_unreadable_import,
            "renaming back to a readable name must clear the flag",
        )

    def test_flagged_row_is_hidden_from_publicly_visible(self):
        junk = self._dest("兰巴拉")
        legit = self._dest("Pokhara")
        self.assertTrue(junk.is_unreadable_import)

        visible = Destination.publicly_visible()
        self.assertIn(legit, visible)
        self.assertNotIn(junk, visible)

    def test_flag_matches_regex_over_a_real_queryset(self):
        """The stored flag must equal the regex verdict, row for row."""
        self._dest("兰巴拉")
        self._dest("더 노스 페이스 인")
        self._dest("मकालु 马卡鲁峰")
        self._dest("Pokhara")

        by_regex = set(
            Destination.objects.filter(
                is_active=True, status=Destination.SubmissionStatus.APPROVED
            )
            .filter(name__regex="[一-鿿가-힯]")
            .exclude(name__regex="[A-Za-zऀ-ॿ]")
            .values_list("pk", flat=True)
        )
        by_flag = set(
            Destination.objects.filter(
                is_unreadable_import=True
            ).values_list("pk", flat=True)
        )
        self.assertEqual(
            by_regex,
            by_flag,
            "the cached flag and the original regex must select identical rows",
        )

    def test_inactive_or_unapproved_rows_stay_hidden(self):
        draft = self._dest("Pokhara", status=Destination.SubmissionStatus.DRAFT)
        off = self._dest("Bhaktapur", is_active=False)
        good = self._dest("Patan")

        visible = Destination.publicly_visible()
        self.assertIn(good, visible)
        self.assertNotIn(draft, visible)
        self.assertNotIn(off, visible)
