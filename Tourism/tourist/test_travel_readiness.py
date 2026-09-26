"""Tests for official travel data: NRB forex, DEM elevations, travel
requirements (visa / TIMS / permits / park & heritage fees), the related
API endpoints, budget enrichment and itinerary trip-readiness.

No test touches the network: NRB / Open-Meteo calls are mocked.
"""
from datetime import date
from decimal import Decimal
from unittest.mock import Mock, patch

from django.core.cache import cache
from django.test import TestCase
from rest_framework.test import APIClient

from . import elevation, fx, travel_requirements as tr
from .models import Category, Destination, ForexRateSnapshot, User

NRB_ENTRY = {
    "date": "2030-01-02",
    "published_on": "2030-01-02 00:00:40",
    "rates": [
        {"currency": {"iso3": "USD", "name": "U.S. Dollar", "unit": 1}, "buy": "150.00", "sell": "150.60"},
        {"currency": {"iso3": "INR", "name": "Indian Rupee", "unit": 100}, "buy": "160.00", "sell": "160.15"},
        {"currency": {"iso3": "EUR", "name": "European Euro", "unit": 1}, "buy": "175.00", "sell": "175.70"},
        {"currency": {"iso3": "JPY", "name": "Japanese Yen", "unit": 10}, "buy": "9.60", "sell": "9.65"},
    ],
}


def no_network():
    """Patch the NRB fetch so tests never hit the network."""
    return patch("tourist.fx.fetch_from_nrb", side_effect=RuntimeError("network disabled in tests"))


class ForexTests(TestCase):
    def setUp(self):
        cache.clear()
        ForexRateSnapshot.objects.all().delete()
        fx.store_payload_entries([NRB_ENTRY], "https://www.nrb.org.np/api/forex/v1/rates?test")
        self.snap = ForexRateSnapshot.objects.get(rate_date=date(2030, 1, 2))

    def test_unit_normalisation(self):
        self.assertEqual(fx.npr_per_unit(self.snap, "USD"), Decimal("150.00"))
        self.assertEqual(fx.npr_per_unit(self.snap, "INR"), Decimal("1.60"))  # 160 per 100
        self.assertEqual(fx.npr_per_unit(self.snap, "JPY"), Decimal("0.96"))  # 9.60 per 10
        self.assertEqual(fx.npr_per_unit(self.snap, "NPR"), Decimal(1))
        self.assertIsNone(fx.npr_per_unit(self.snap, "XYZ"))

    def test_convert_via_npr(self):
        self.assertAlmostEqual(fx.convert(100, "USD", "NPR", self.snap), 15000.0)
        self.assertAlmostEqual(fx.convert(100, "USD", "EUR", self.snap), 100 * 150 / 175)
        self.assertAlmostEqual(fx.convert(1000, "NPR", "INR", self.snap), 625.0)
        self.assertIsNone(fx.convert(100, "USD", "XYZ", self.snap))

    def test_no_fixed_fallback_rate(self):
        ForexRateSnapshot.objects.all().delete()
        with no_network():
            self.assertIsNone(fx.latest_snapshot())
            self.assertIsNone(fx.convert(100, "USD", "NPR"))
            meta = fx.snapshot_meta(None)
        self.assertFalse(meta["available"])

    def test_failed_fetch_backs_off(self):
        ForexRateSnapshot.objects.all().delete()
        with no_network() as fetch:
            fx.latest_snapshot()
            fx.latest_snapshot()
        self.assertEqual(fetch.call_count, 1)  # second call inside the 1h backoff

    def test_fetch_from_nrb_parses_payload(self):
        ForexRateSnapshot.objects.all().delete()
        response = Mock(status_code=200)
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"data": {"payload": [NRB_ENTRY]}})
        with patch("requests.get", return_value=response) as get:
            stored = fx.fetch_from_nrb(days_back=3)
        self.assertEqual(len(stored), 1)
        self.assertIn("nrb.org.np", get.call_args[0][0])
        self.assertEqual(ForexRateSnapshot.objects.get().rates["USD"]["buy"], "150.00")

    def test_rates_endpoint(self):
        with no_network():
            res = APIClient().get("/api/v1/fx/rates/")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["available"])
        self.assertEqual(body["source"], "Nepal Rastra Bank")
        self.assertEqual(body["rate_date"], "2030-01-02")
        self.assertAlmostEqual(body["currencies"]["INR"]["npr_per_unit"], 1.6)

    def test_rates_endpoint_unavailable(self):
        ForexRateSnapshot.objects.all().delete()
        with no_network():
            res = APIClient().get("/api/v1/fx/rates/")
        self.assertEqual(res.status_code, 503)
        self.assertFalse(res.json()["available"])


class ElevationTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(email="elev-admin@example.com", password="AdminPass123!")
        self.category = Category.objects.create(name="Trekking")

    def make(self, name, lat, lon, **extra):
        return Destination.objects.create(
            name=name, category=self.category, description="x", latitude=lat, longitude=lon,
            created_by=self.admin, status=Destination.SubmissionStatus.APPROVED, is_active=True, **extra)

    def test_precision_guard(self):
        self.assertTrue(elevation.coordinate_precision_ok(27.805, 86.712))
        self.assertFalse(elevation.coordinate_precision_ok(27.8, 86.7))          # too coarse
        self.assertFalse(elevation.coordinate_precision_ok(28.0833, 85.4167))    # whole arc-minutes
        self.assertFalse(elevation.coordinate_precision_ok(40.123, 86.712))      # outside Nepal
        self.assertFalse(elevation.coordinate_precision_ok(None, 86.712))

    def test_parse_altitude_text(self):
        self.assertEqual(elevation.parse_altitude_text("3,440 m"), 3440)
        self.assertEqual(elevation.parse_altitude_text("approx 827 metres"), 827)
        self.assertIsNone(elevation.parse_altitude_text("high up"))

    def test_apply_records_checks_coordinates(self):
        ok = self.make("Namche Test", 27.805, 86.712)
        moved = self.make("Moved Test", 27.9, 86.8)
        coarse = self.make("Coarse Test", 27.8, 86.7)
        stats = elevation.apply_records([
            {"id": ok.id, "lat": 27.805, "lon": 86.712, "elevation_m": 3478, "retrieved_at": "2026-09-26"},
            {"id": moved.id, "lat": 27.95, "lon": 86.85, "elevation_m": 4000},
            {"id": coarse.id, "lat": 27.8, "lon": 86.7, "elevation_m": 4000},
            {"id": ok.id + 999999, "lat": 1, "lon": 1, "elevation_m": 1},
        ])
        self.assertEqual((stats["applied"], stats["moved"], stats["imprecise"], stats["missing"]), (1, 1, 1, 1))
        ok.refresh_from_db()
        self.assertEqual(ok.elevation_m, 3478)
        self.assertEqual(elevation.best_elevation(ok)["kind"], "dem")
        coarse.refresh_from_db()
        self.assertIsNone(coarse.elevation_m)

    def test_fetch_batch_mocked(self):
        response = Mock()
        response.raise_for_status = Mock()
        response.json = Mock(return_value={"elevation": [3478.0, 809.0]})
        with patch("requests.get", return_value=response) as get:
            values = elevation.fetch_batch([(27.805, 86.712), (28.209, 83.959)])
        self.assertEqual(values, [3478.0, 809.0])
        self.assertIn("api.open-meteo.com/v1/elevation", get.call_args[0][0])


class TravelRequirementsTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser(email="req-admin@example.com", password="AdminPass123!")
        self.category = Category.objects.create(name="Trekking")
        ForexRateSnapshot.objects.all().delete()
        fx.store_payload_entries([NRB_ENTRY], "https://www.nrb.org.np/api/forex/v1/rates?test")

    def make(self, name, district, lat=28.0, lon=84.0, **extra):
        return Destination.objects.create(
            name=name, category=self.category, description="x", latitude=lat, longitude=lon, district=district,
            created_by=self.admin, status=Destination.SubmissionStatus.APPROVED, is_active=True, **extra)

    def test_dataset_is_sourced(self):
        data = tr.load_dataset()
        for key in ("doi_visa", "ntb_tims", "ntb_parks", "ntb_heritage", "doi_permits"):
            self.assertTrue(data["sources"][key]["url"].startswith("https://"), key)
        for area in data["protected_areas"]:
            self.assertIn("foreign", area["fees_npr"], area["name"])

    def test_nationality_normalisation(self):
        self.assertEqual(tr.normalize_nationality("India"), "saarc")
        self.assertEqual(tr.normalize_nationality("CN"), "chinese")
        self.assertEqual(tr.normalize_nationality("nepali"), "nepali")
        self.assertEqual(tr.normalize_nationality("Germany"), "foreign")

    def test_upper_mustang_fees(self):
        dest = self.make("Upper Mustang Trek", "Mustang", 29.183, 83.951)
        req = tr.destination_requirements(dest, nationality="foreign", days=10, month=10, travelers=2)
        self.assertEqual([p["name"] for p in req["protected_areas"]], ["Annapurna Conservation Area"])
        self.assertEqual([r["name"] for r in req["restricted_areas"]], ["Upper Mustang"])
        self.assertEqual(req["tims"]["region"], "Mustang Region")
        totals = tr.fee_totals(req["fees"], 2)
        # ACA 3000 + TIMS 2000 + Upper Mustang US$500 at NPR 150.00
        self.assertAlmostEqual(totals["per_person_npr"], 3000 + 2000 + 500 * 150.0)
        self.assertAlmostEqual(totals["group_npr"], 2 * totals["per_person_npr"])
        self.assertTrue(all(line.get("source", {}).get("url") for line in totals["lines"]))

    def test_saarc_everest_fees(self):
        dest = self.make("Namche Bazaar", "Solukhumbu", 27.805, 86.712)
        req = tr.destination_requirements(dest, nationality="saarc", days=12)
        self.assertEqual([p["name"] for p in req["protected_areas"]], ["Sagarmatha National Park"])
        self.assertEqual(req["tims"]["fee_npr"], 1000)
        self.assertAlmostEqual(tr.fee_totals(req["fees"], 1)["per_person_npr"], 2500)

    def test_lowland_city_has_no_trekking_fees(self):
        dest = self.make("Pokhara Lakeside Cycling", "Kaski", 28.21, 83.96)
        req = tr.destination_requirements(dest, nationality="foreign", days=3)
        self.assertEqual(req["restricted_areas"], [])
        self.assertIsNone(req["tims"])
        self.assertEqual(tr.fee_totals(req["fees"], 1)["per_person_npr"], 0)

    def test_heritage_matching(self):
        dest = self.make("Bhaktapur Durbar Square", "Bhaktapur", 27.672, 85.428)
        req = tr.destination_requirements(dest, nationality="foreign")
        self.assertEqual(req["heritage_sites"][0]["fee_npr"], 1800)
        self.assertEqual(req["heritage_sites"][0]["status"], "likely")

    def test_restricted_fee_rules(self):
        self.assertEqual(tr.estimate_restricted_fee_usd({"type": "per_day", "usd": 50}, 10, None)["usd"], 500)
        seasonal = {"type": "seasonal_weekly", "peak_months": [9, 10, 11], "peak_week_usd": 100,
                    "peak_extra_day_usd": 15, "off_week_usd": 75, "off_extra_day_usd": 10}
        self.assertEqual(tr.estimate_restricted_fee_usd(seasonal, 9, 10)["usd"], 130)
        self.assertEqual(tr.estimate_restricted_fee_usd(seasonal, 9, 1)["usd"], 95)
        self.assertIn("no travel month", tr.estimate_restricted_fee_usd(seasonal, 7, None)["note"])
        self.assertIsNone(tr.estimate_restricted_fee_usd({"type": "per_day", "usd": 50}, 0, None))

    def test_visa_tiers(self):
        self.assertEqual(tr.visa_summary("foreign", 10)["fee_usd_for_stay"]["usd"], 30)
        self.assertEqual(tr.visa_summary("foreign", 20)["fee_usd_for_stay"]["usd"], 50)
        self.assertFalse(tr.visa_summary("nepali", 10)["applies"])

    def test_requirement_endpoints(self):
        dest = self.make("Namche Bazaar", "Solukhumbu", 27.805, 86.712)
        hidden = Destination.objects.create(name="Draft Place", category=self.category, description="x",
                                            latitude=27.8, longitude=86.7, created_by=self.admin, is_active=True,
                                            status=Destination.SubmissionStatus.PENDING)
        client = APIClient()
        with no_network():
            general = client.get("/api/v1/travel-requirements/?nationality=saarc")
            detail = client.get(f"/api/v1/travel-requirements/destination/{dest.id}/?nationality=foreign&days=12&travelers=2")
            draft = client.get(f"/api/v1/travel-requirements/destination/{hidden.id}/")
        self.assertEqual(general.status_code, 200)
        self.assertEqual(general.json()["nationality"], "saarc")
        self.assertEqual(detail.status_code, 200)
        self.assertAlmostEqual(detail.json()["fee_totals"]["group_npr"], 2 * (3000 + 2000))
        self.assertEqual(draft.status_code, 404)


class BudgetAndItineraryReadinessTests(TestCase):
    def setUp(self):
        cache.clear()
        self.admin = User.objects.create_superuser(email="trip-admin@example.com", password="AdminPass123!")
        self.category = Category.objects.create(name="Trekking")
        ForexRateSnapshot.objects.all().delete()
        fx.store_payload_entries([NRB_ENTRY], "https://www.nrb.org.np/api/forex/v1/rates?test")
        self.mustang = Destination.objects.create(
            name="Upper Mustang Trek", category=self.category, description="trek", latitude=29.183, longitude=83.951,
            district="Mustang", city="Lo Manthang", created_by=self.admin,
            status=Destination.SubmissionStatus.APPROVED, is_active=True, elevation_m=3818,
            elevation_source=elevation.DEM_SOURCE)

    def test_budget_uses_nrb_and_official_fees(self):
        ml = {"known_cost_total_usd": 400.0, "breakdown": {"accommodation": 150.0, "food": 120.0, "transport": 130.0},
              "estimated_total": None, "total_budget_usd": None}
        with no_network(), patch("tourist.views_ml.get_ml_budget_prediction", return_value=ml):
            res = APIClient().post("/api/v1/ml/budget/", {
                "destination": self.mustang.id, "days": 10, "travelers": 2, "nationality": "foreign", "travel_month": 10,
            }, format="json")
        self.assertEqual(res.status_code, 200, res.content)
        body = res.json()
        self.assertEqual(body["exchange_rate"]["usd_to_npr"], 150.0)
        self.assertEqual(body["exchange_rate"]["source"], "Nepal Rastra Bank")
        self.assertAlmostEqual(body["known_cost_total_npr"], 60000.0)
        labels = [line["label"] for line in body["official_fees"]["lines"]]
        self.assertTrue(labels[0].startswith("Nepal tourist visa"))
        self.assertIn("Restricted-area permit — Upper Mustang", labels)
        fees_pp = 30 * 150 + 3000 + 500 * 150 + 2000
        self.assertAlmostEqual(body["official_fees"]["per_person_npr"], fees_pp)
        self.assertAlmostEqual(body["trip_total_npr"], 60000 + 2 * fees_pp)
        self.assertAlmostEqual(body["per_person_npr"], body["trip_total_npr"] / 2)
        self.assertEqual(body["matched_destination"]["id"], self.mustang.id)

    def test_budget_without_rate_reports_unavailable(self):
        ForexRateSnapshot.objects.all().delete()
        ml = {"known_cost_total_usd": 100.0, "breakdown": {"food": 100.0}}
        with no_network(), patch("tourist.views_ml.get_ml_budget_prediction", return_value=ml):
            res = APIClient().post("/api/v1/ml/budget/", {"destination": self.mustang.id, "days": 3}, format="json")
        body = res.json()
        self.assertFalse(body["exchange_rate"]["available"])
        self.assertIsNone(body["known_cost_total_npr"])
        self.assertIsNone(body["trip_total_npr"])

    def test_budget_when_ml_down_still_returns_official_fees(self):
        with no_network(), patch("tourist.views_ml.get_ml_budget_prediction", return_value=None):
            res = APIClient().post("/api/v1/ml/budget/", {"destination": self.mustang.id, "days": 10, "travelers": 1},
                                   format="json")
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertFalse(body["living_costs_available"])
        self.assertIsNone(body["trip_total_npr"])  # never invented
        self.assertGreater(body["official_fees"]["group_npr"], 0)
        with patch("tourist.views_ml.get_ml_budget_prediction", return_value=None):
            res = APIClient().post("/api/v1/ml/budget/", {"city": "Nowhere", "days": 3}, format="json")
        self.assertEqual(res.status_code, 503)

    def test_itinerary_readiness(self):
        low = Destination.objects.create(
            name="Jomsom Airport Walk", category=self.category, description="trek", latitude=28.781, longitude=83.723,
            district="Mustang", city="Jomsom", created_by=self.admin,
            status=Destination.SubmissionStatus.APPROVED, is_active=True, elevation_m=2735,
            elevation_source=elevation.DEM_SOURCE)
        with no_network(), patch("tourist.views_ml.requests.post", side_effect=__import__("requests").RequestException("down")):
            res = APIClient().post("/api/v1/ml/itinerary/", {
                "days": 2, "travelers": 2, "start_city": "Mustang", "district": "Mustang", "interests": ["trek"],
                "nationality": "foreign", "travel_month": 10,
            }, format="json")
        self.assertEqual(res.status_code, 200, res.content)
        body = res.json()
        profile = body["altitude_profile"]["days"]
        self.assertEqual([d["max_elevation_m"] for d in profile], [2735, 3818])  # low -> high ordering
        self.assertTrue(any(w["type"] == "fast_ascent" for w in body["acclimatization"]["warnings"]))
        self.assertEqual([r["name"] for r in body["permits_and_fees"]["restricted_areas"]], ["Upper Mustang"])
        keys = [item["key"] for item in body["trip_readiness"]]
        self.assertIn("visa", keys)
        self.assertIn("tims", keys)
        self.assertIn("altitude", keys)
        self.assertTrue(body["why_this_itinerary"])
        self.assertTrue(low.id)


class PlaceholderPhoneTests(TestCase):
    def test_detector(self):
        from .phone_quality import is_placeholder_phone

        for fake in ("+977-037-520123", "089-420123", "87520123.0", "977025560123.0"):
            self.assertTrue(is_placeholder_phone(fake), fake)
        for real in ("+977-01-4221119", "+977-056-523911", "1144", "100", "", None):
            self.assertFalse(is_placeholder_phone(real), real)

    def test_serializer_hides_placeholder(self):
        from .models import Hospital
        from .serializers import HospitalSerializer

        h = Hospital(name="Test District Hospital", phone="+977-037-520123", latitude=27.3, longitude=86.5)
        self.assertEqual(HospitalSerializer(h).data["phone"], "")
        h.phone = "+977-01-4221119"
        self.assertEqual(HospitalSerializer(h).data["phone"], "+977-01-4221119")
