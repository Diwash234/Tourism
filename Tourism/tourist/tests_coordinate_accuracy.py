"""A coordinate's stored precision is not its real precision, and the API
must not imply otherwise.

The catalog exposes ``coordinate_accuracy`` so a client can tell a surveyed
position from a town centroid. Two things undermined that:

* 1323 destinations had no label at all, leaving the field the UI reads empty;
* the import pads coordinates with trailing zeros, so "28.500000" looks like a
  six-decimal survey but carries one decimal of information. Counting decimals
  naively would have labelled those as exact.

These tests pin the classification and the backfill.
"""
from django.apps import apps
from django.test import TestCase

from .coordinate_accuracy import (
    ACCURACY_AREA,
    ACCURACY_EXACT,
    ACCURACY_MODERATE,
    classify_precision,
    decimals,
    in_nepal,
    is_whole_arc_minute,
    resolution_km,
)


class DecimalCountingTests(TestCase):
    def test_trailing_zeros_carry_no_precision(self):
        # The import pads coordinates, so the padded form must not be trusted.
        self.assertEqual(decimals("28.500000"), 1)
        self.assertEqual(decimals("28.500"), 1)
        self.assertEqual(decimals("27.889700"), 4)
        self.assertEqual(decimals("28.2096"), 4)

    def test_plain_values(self):
        self.assertEqual(decimals("28"), 0)
        self.assertEqual(decimals("28.5"), 1)
        self.assertEqual(decimals("28.2096"), 4)
        self.assertEqual(decimals(None), 0)
        self.assertEqual(decimals(""), 0)

    def test_whole_arc_minutes_are_detected_despite_four_decimals(self):
        self.assertTrue(is_whole_arc_minute("28.0833"))
        self.assertTrue(is_whole_arc_minute("85.4167"))
        self.assertFalse(is_whole_arc_minute("28.2096"))
        self.assertFalse(is_whole_arc_minute(27.8897))

    def test_nepal_bounds(self):
        self.assertTrue(in_nepal(28.2096, 83.9856))
        self.assertFalse(in_nepal(40.7128, -74.0060))
        self.assertFalse(in_nepal("abc", 83.0))


class PrecisionClassificationTests(TestCase):
    def test_surveyed_position(self):
        self.assertEqual(classify_precision("27.8897", "87.0888"), ACCURACY_EXACT)

    def test_three_decimals_is_a_usable_pin(self):
        self.assertEqual(classify_precision("28.209", "83.985"), ACCURACY_MODERATE)

    def test_padded_low_precision_is_an_area_point_not_a_survey(self):
        # This is the padded form that naive decimal counting gets wrong.
        self.assertEqual(classify_precision("28.500000", "84.000000"), ACCURACY_AREA)

    def test_coarse_values_are_area_points(self):
        for lat, lon in (("28.5", "84.0"), ("27.0", "85.0"), ("28.50", "84.00")):
            with self.subTest(lat=lat, lon=lon):
                self.assertEqual(classify_precision(lat, lon), ACCURACY_AREA)

    def test_arc_minute_grid_is_an_area_point_even_at_four_decimals(self):
        self.assertEqual(classify_precision("28.0833", "85.4167"), ACCURACY_AREA)

    def test_unusable_coordinates_are_never_optimistic(self):
        for lat, lon in (("", ""), (None, None), ("91.0", "181.0")):
            with self.subTest(lat=lat, lon=lon):
                self.assertEqual(classify_precision(lat, lon), ACCURACY_AREA)

    def test_weakest_coordinate_decides(self):
        # One precise axis does not make a pair precise.
        self.assertEqual(classify_precision("27.889700", "84.0"), ACCURACY_AREA)


class DistanceResolutionTests(TestCase):
    """A distance is only as precise as the pin it points at.

    Reporting "0.34 km" to a destination stored to two decimals states more
    precision than the data holds, so the resolution travels with the distance.
    """

    def test_resolution_tracks_the_stored_precision(self):
        cases = [
            (("28.2096", "83.9856"), 0.0111),   # four decimals, ~11 m
            (("28.209", "83.985"), 0.111),      # three decimals, ~111 m
            (("28.53", "84.21"), 1.11),         # two decimals, ~1.1 km
            (("28.5", "84.2"), 11.1),           # one decimal
            (("27.0", "85.0"), 111.0),          # whole degrees
        ]
        for (lat, lon), expected in cases:
            with self.subTest(lat=lat, lon=lon):
                self.assertAlmostEqual(resolution_km(lat, lon), expected, places=3)

    def test_padded_zeros_do_not_buy_precision(self):
        self.assertAlmostEqual(
            resolution_km("28.500000", "84.200000"), resolution_km("28.5", "84.2"), places=4
        )

    def test_arc_minute_data_is_coarse_despite_four_decimals(self):
        self.assertAlmostEqual(resolution_km("28.4667", "83.9333"), 1.85, places=2)

    def test_unusable_coordinates_report_no_resolution(self):
        for lat, lon in (("", ""), (None, None), ("91.0", "181.0")):
            with self.subTest(lat=lat, lon=lon):
                self.assertIsNone(resolution_km(lat, lon))


class _RecordingSchemaEditor:
    def __init__(self):
        self.statements = []

    def execute(self, statement, *args, **kwargs):
        self.statements.append(statement)


class CoordinateAccuracyBackfillTests(TestCase):
    def setUp(self):
        from .models import Category, User

        user = User.objects.create_superuser("coord-qa@test.local", "CoordQA!123")
        self.category = Category.objects.create(name="Coord QA")
        self.user = user

    def _destination(self, name, lat, lon, accuracy=""):
        from .models import Destination

        return Destination.objects.create(
            name=name, slug=name.lower().replace(" ", "-"), category=self.category,
            description="Fixture for coordinate accuracy tests.",
            latitude=lat, longitude=lon, coordinate_accuracy=accuracy, created_by=self.user,
        )

    def _run(self):
        from importlib import import_module

        module = import_module("tourist.migrations.0087_derive_coordinate_accuracy")
        editor = _RecordingSchemaEditor()
        module.fill(apps, editor)
        return editor

    def test_blank_labels_are_filled_from_the_coordinate(self):
        self._destination("Surveyed Peak", "27.889700", "87.088800")
        self._destination("Padded Village", "28.500000", "84.000000")
        self._destination("Mid Pin", "28.209", "83.985")
        self._run()
        from .models import Destination

        self.assertEqual(
            Destination.objects.get(name="Surveyed Peak").coordinate_accuracy, ACCURACY_EXACT
        )
        self.assertEqual(
            Destination.objects.get(name="Padded Village").coordinate_accuracy, ACCURACY_AREA
        )
        self.assertEqual(
            Destination.objects.get(name="Mid Pin").coordinate_accuracy, ACCURACY_MODERATE
        )

    def test_existing_human_label_is_never_overwritten(self):
        # "Moderate" on a coarse coordinate looks wrong, but it may be a
        # deliberate human judgement and must survive the backfill.
        self._destination("Judged", "28.5", "84.0", accuracy="Reviewed by field team")
        self._run()
        from .models import Destination

        self.assertEqual(
            Destination.objects.get(name="Judged").coordinate_accuracy,
            "Reviewed by field team",
        )

    def test_backfill_is_idempotent(self):
        self._destination("Twice", "27.889700", "87.088800")
        self._run()
        self._run()
        from .models import Destination

        self.assertEqual(
            Destination.objects.get(name="Twice").coordinate_accuracy, ACCURACY_EXACT
        )

    def test_backfill_reports_what_it_filled(self):
        self._destination("Reported", "28.500000", "84.000000")
        editor = self._run()
        self.assertTrue(editor.statements)
        self.assertIn(ACCURACY_AREA, editor.statements[0])
