"""A photograph must be of the place it is attached to.

19,791 of the 20,168 real image rows in the library were the same photograph
reused across destinations -- one SAARC Secretariat picture on 331 places, a
Patan Durbar Square picture on 236. Only 377 rows were attached to exactly one
place, covering 2.6% of publishable destinations.

These tests pin the rule that decides whether a candidate photograph genuinely
depicts a destination, because that rule is the only thing standing between a
traveller and a confidently-labelled photograph of somewhere else.
"""
from django.test import SimpleTestCase

from tourist.photo_matching import match_score, tokens


class TokenTests(SimpleTestCase):
    def test_generic_words_are_ignored(self):
        # "Nepal", "sunset", "over" and "photo" identify nothing, on either side.
        self.assertEqual(tokens("Sunset over Phewa Lake, Nepal"), {"phewa", "lake"})

    def test_short_words_are_ignored(self):
        self.assertEqual(tokens("Tansen at Palpa"), {"tansen", "palpa"})

    def test_significant_words_survive(self):
        # "at" and "night" are describing the shot, not identifying the place.
        self.assertEqual(
            tokens("Patan Durbar Square at night, Lalitpur"),
            {"patan", "durbar", "square", "lalitpur"},
        )


class MatchScoreTests(SimpleTestCase):
    def test_exact_name_matches(self):
        self.assertEqual(match_score("Patan Durbar Square", "Patan Durbar Square, Lalitpur"), 1.0)
        self.assertEqual(match_score("Swayambhunath", "Swayambhunath temple, Kathmandu"), 1.0)
        self.assertEqual(match_score("Annapurna Massif", "Aerial view of the Annapurna Massif"), 1.0)

    def test_number_drift_between_name_and_caption_still_matches(self):
        # Catalogue "Davis Falls" vs a photograph titled "Davis Fall".
        self.assertEqual(match_score("Davis Falls", "Davis Fall, Nepal-WLV-1752"), 1.0)

    def test_a_different_place_is_rejected(self):
        # The near-miss that matters: a different fall, a different square.
        self.assertEqual(match_score("Davis Falls", "Davis Lake, California"), 0.0)
        self.assertEqual(match_score("Patan Museum", "Patan Durbar Square at night"), 0.0)
        self.assertEqual(match_score("Machhapuchhare", "Aerial view of the Annapurna Massif"), 0.0)

    def test_partial_overlap_is_rejected(self):
        # Sharing one word is not evidence.
        self.assertEqual(match_score("Gorkha Durbar", "Gorkha fortress seen from the ridge"), 0.0)
        self.assertEqual(match_score("Pokhara", "Sunrise over Phewa Lake"), 0.0)

    def test_empty_inputs_are_rejected(self):
        self.assertEqual(match_score("", "anything"), 0.0)
        self.assertEqual(match_score("Patan Museum", ""), 0.0)
        self.assertEqual(match_score("!!! ???", "Patan Museum"), 0.0)

    def test_a_name_made_only_of_generic_words_is_rejected(self):
        # Nothing distinctive to match on, so nothing may be claimed.
        self.assertEqual(match_score("Nepal", "Nepal sunset photo"), 0.0)

    def test_documented_trade_off_plural_region_against_single_feature(self):
        # Accepted on purpose: a missing photo is a visible gap, a wrong photo is
        # a false statement, and the gap is the cheaper failure. See the module
        # docstring; narrowing this needs per-destination review, not a rule.
        self.assertEqual(match_score("Pokhara Lakes", "Phewa Lake, Pokhara"), 1.0)
