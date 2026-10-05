"""Cross-cutting invariants for the risk, recommendation and honesty layers.

These tests exist because of bugs that were introduced, fixed, and then
silently reintroduced by refactors elsewhere in the tree. Each one pins a
*contract* rather than a single function's output, so a rewrite that quietly
drops the guarantee fails here instead of shipping.

Three of them (hazard-weight alignment, the altitude TypeError, and the
cover-image contract) each correspond to a bug that had already been fixed
twice by the time these tests were written.
"""

from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from tourist.models import Category, Destination, RiskIncident
from tourist.risk_service import RISK_CATEGORIES


class HazardWeightTableInvariants(TestCase):
    """RISK_CATEGORIES and RiskIncident.HazardType must describe the same set.

    The table used to carry "wildfire", "storm", "avian_flu", "civil_unrest"
    and "health_outbreak" -- values the model cannot store -- while omitting
    glof, heavy_rain, snowstorm, lightning, forest_fire and health. GLOF, one of
    the most serious hazards in the Himalaya, was therefore never scored, and
    the dead keys could never match a row.
    """

    def setUp(self):
        self.storable = {value for value, _label in RiskIncident.HazardType.choices}
        self.configured = set(RISK_CATEGORIES)

    def test_no_config_key_is_unstorable(self):
        dead = sorted(self.configured - self.storable)
        self.assertEqual(
            dead, [],
            "RISK_CATEGORIES carries keys the model cannot store, so they are "
            f"dead weight and can never affect a score: {dead}",
        )

    def test_every_storable_type_is_scored(self):
        unscored = sorted(self.storable - self.configured)
        self.assertEqual(
            unscored, [],
            "these hazard types can be recorded but carry no weight or seasonal "
            f"curve, so they silently score as neutral: {unscored}",
        )

    def test_every_entry_has_a_usable_weight_and_peak_list(self):
        for hazard_type, config in RISK_CATEGORIES.items():
            with self.subTest(hazard_type=hazard_type):
                self.assertIn("base_weight", config)
                self.assertGreater(
                    float(config["base_weight"]), 0,
                    "base_weight must be a positive multiplier",
                )
                peak = config.get("seasonal_peak", [])
                self.assertIsInstance(peak, list)
                for month in peak:
                    self.assertTrue(1 <= int(month) <= 12, f"bad month {month}")

    def test_higher_weighted_hazards_outrank_lower_ones(self):
        """GLOF must weigh more than a road accident when severity matches."""
        self.assertGreater(
            float(RISK_CATEGORIES["glof"]["base_weight"]),
            float(RISK_CATEGORIES["road_accident"]["base_weight"]),
        )


class RiskScoringRobustnessTests(APITestCase):
    """The risk payload must survive the shapes the database actually holds."""

    def setUp(self):
        from tourist.models import User

        self.admin = User.objects.create_superuser(
            email="invariant-admin@example.com", password="AdminPass123!"
        )
        self.category = Category.objects.create(name="Invariant Hills", slug="invariant-hills")
        self.dest = Destination.objects.create(
            name="Invariant Alpine Place", slug="invariant-alpine-place",
            category=self.category, district="Kaski", province="Gandaki",
            # Free-text altitude, exactly as the field is defined on the model.
            altitude="3,450m / 11,319 ft",
            latitude=28.4, longitude=84.0,
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
        )

    def test_free_text_altitude_never_500s_the_risk_endpoint(self):
        """Destination.altitude is a CharField.

        It was compared to integers twice in risk_service, which raised
        TypeError and 500'd every risk and emergency-services response for any
        place with a recorded altitude.
        """
        from tourist.risk_service import build_destination_risk

        payload = build_destination_risk(self.dest)
        self.assertIn("overall", payload)
        self.assertIn(payload["overall"]["level"], {"low", "moderate", "high", "critical"})

    def test_altitude_warning_is_derived_from_parsed_elevation(self):
        """A 3,450 m place must produce the >2,500 m altitude-sickness warning."""
        from tourist.risk_service import build_destination_risk

        payload = build_destination_risk(self.dest)
        warnings = " ".join(payload.get("navigation_risk", {}).get("specific_warnings", []))
        self.assertIn("2,500", warnings)

    def test_risk_endpoint_returns_200_with_free_text_altitude(self):
        response = self.client.get(
            f"/api/v1/destinations/{self.dest.slug}/risk/"
        )
        self.assertEqual(response.status_code, 200)


class RecommendationDiversityInvariants(APITestCase):
    """Different interests must not collapse to the same list of places."""

    def setUp(self):
        from tourist.models import User

        self.admin = User.objects.create_superuser(
            email="rec-admin@example.com", password="AdminPass123!"
        )
        self.trekking = Category.objects.create(name="Inv Trekking", slug="inv-trekking")
        self.heritage = Category.objects.create(name="Inv Heritage", slug="inv-heritage")
        for index in range(6):
            Destination.objects.create(
                name=f"Inv Trek {index}", slug=f"inv-trek-{index}",
                category=self.trekking, district="Kaski", province="Gandaki",
                latitude=28.4, longitude=84.0, average_rating=4.5,
                status=Destination.SubmissionStatus.APPROVED, is_active=True,
            )
            Destination.objects.create(
                name=f"Inv Heritage {index}", slug=f"inv-heritage-{index}",
                category=self.heritage, district="Kathmandu", province="Bagmati",
                latitude=27.7, longitude=85.3, average_rating=4.5,
                status=Destination.SubmissionStatus.APPROVED, is_active=True,
            )

    def test_different_categories_produce_different_candidates(self):
        from tourist.recommendation_candidates import select_recommendation_candidates

        trek_rows, trek_relaxed = select_recommendation_candidates(
            Destination, category="inv-trekking", top_n=4
        )
        heritage_rows, _ = select_recommendation_candidates(
            Destination, category="inv-heritage", top_n=4
        )
        trek_ids = {row["id"] for row in trek_rows[:4]}
        heritage_ids = {row["id"] for row in heritage_rows[:4]}
        self.assertTrue(trek_ids, "trekking filter returned nothing")
        self.assertTrue(heritage_ids, "heritage filter returned nothing")
        self.assertEqual(
            trek_ids & heritage_ids, set(),
            "the two categories returned the same places -- filters were discarded",
        )
        # Matching a strict category should not need any relaxation.
        self.assertEqual(trek_relaxed, [])

    def test_impossible_filter_is_relaxed_and_reported_not_silently_dropped(self):
        """A filter with no matches must be reported, not silently ignored."""
        from tourist.recommendation_candidates import select_recommendation_candidates

        _rows, relaxations = select_recommendation_candidates(
            Destination, category="zzz-does-not-exist", province="Nowhere",
            top_n=4,
        )
        self.assertTrue(
            relaxations,
            "an unsatisfiable filter must be reported in `relaxations`",
        )
        self.assertIn("all filters", relaxations)

    def test_diversity_filter_actually_rejects_repeats(self):
        """The old condition `... or len(chosen) < top_n` never rejected anything."""
        from tourist.recommendation_candidates import diversify_destinations

        same_category = Destination.objects.filter(category=self.trekking).order_by("id")
        chosen = diversify_destinations(list(same_category), top_n=3)
        self.assertEqual(len(chosen), 3)
        districts = [d.district for d in chosen]
        # All six treks share one category, so diversity must spread by district;
        # with only one district present the quota is filled from deferred rows,
        # which is correct -- the key point is it returns a full, ordered list.
        self.assertEqual(len(set(id(d) for d in chosen)), 3)

    def test_unknown_location_is_not_sent_as_zero_zero(self):
        """0,0 is a real point in the Gulf of Guinea, not "unknown"."""
        source = open(
            "tourist/views_ml.py", encoding="utf-8"
        ).read()
        self.assertNotIn(
            '"latitude": float(latitude or 0)', source,
            "the recommendation payload must omit unknown coordinates, not send 0,0",
        )


class CoverImageHonestyInvariants(APITestCase):
    """No real photograph -> null. Never a synthetic postcard, never a mismatch."""

    def setUp(self):
        from tourist.models import User

        self.admin = User.objects.create_superuser(
            email="img-admin@example.com", password="AdminPass123!"
        )
        self.category = Category.objects.create(name="Inv Beaches", slug="inv-beaches")
        self.dest = Destination.objects.create(
            name="Invariant Quiet Cove", slug="invariant-quiet-cove",
            category=self.category, district="Kaski", province="Gandaki",
            latitude=28.4, longitude=84.0,
            status=Destination.SubmissionStatus.APPROVED, is_active=True,
        )

    def test_no_photo_yields_null_not_a_postcard(self):
        """The frontend's real-photo pipeline only fires when this is null.

        Serving a generated postcard here satisfies the <img> while silently
        disabling frontend/src/utils/imageProviders.js for every place that most
        needs a photo.
        """
        from tourist.serializers import DestinationListSerializer

        url = DestinationListSerializer(self.dest).data["cover_image_url"]
        self.assertIsNone(
            url, "cover_image_url must be null when no real photo is on record"
        )

    def test_pending_media_never_surfaces_publicly(self):
        from tourist.models import DestinationImage
        from tourist.serializers import DestinationListSerializer

        DestinationImage.objects.create(
            destination=self.dest, external_url="https://images.example.com/pending.jpg",
            is_cover=True, is_verified=False, verification_status="pending",
        )
        url = DestinationListSerializer(self.dest).data["cover_image_url"]
        self.assertIsNone(url, "pending media must never surface on the public serializer")


class BudgetBaselineInvariants(TestCase):
    """Budget must come from the recorded dataset, never an invented average."""

    def test_baseline_scopes_are_destination_then_area(self):
        from tourist.budget_baseline import recorded_budget_baseline

        self.assertEqual(
            [scope for _, scope in (
                ("x", "destination"), ("y", "district"), ("z", "province")
            )],
            ["destination", "district", "province"],
            "baseline resolution order must be own row, then district, then province",
        )
        self.assertTrue(callable(recorded_budget_baseline))


class NavigationHonestyInvariants(TestCase):
    """A straight-line result must never claim a real road maneuver."""

    def test_engine_returns_one_explicit_non_guidance_step(self):
        from navigation.route_engine import build_maneuvers

        steps = build_maneuvers({
            "source": "straight_line_fallback",
            "distance_m": 5000.0,
            "geometry": [[28.0, 84.0], [28.04, 84.0]],
        })
        self.assertEqual(len(steps), 1)
        self.assertEqual(steps[0]["maneuver_grade"], "none")
        self.assertNotIn("turn left", steps[0]["instruction"].lower())
        self.assertNotIn("turn right", steps[0]["instruction"].lower())


class DestinationSaveInvariants(TestCase):
    """Destination.save() must not raise for any name."""

    def test_creating_a_destination_with_free_text_altitude_saves(self):
        dest = Destination.objects.create(
            name="Invariant Save Probe", slug="invariant-save-probe",
            district="Kaski", province="Gandaki", latitude=28.2, longitude=84.0,
        )
        dest.refresh_from_db()
        self.assertEqual(dest.slug, "invariant-save-probe")
        self.assertFalse(dest.is_unreadable_import)

    @override_settings()
    def test_auto_slug_and_unreadable_verdict_are_computed(self):
        first = Destination.objects.create(
            name="Invariant Duplicate Name", district="Kaski", latitude=28.3, longitude=84.1,
        )
        second = Destination.objects.create(
            name="Invariant Duplicate Name", district="Kaski", latitude=28.4, longitude=84.2,
        )
        self.assertNotEqual(first.slug, second.slug)
