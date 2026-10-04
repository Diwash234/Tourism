from unittest import mock

import requests
from django.test import TestCase

from tourist.models import BudgetEstimation, Destination

ML_DOWN = mock.patch("tourist.views_ml.requests.post", side_effect=requests.ConnectionError("ml down"))


def _dest(name, slug, district, province="Gandaki"):
    return Destination.objects.create(name=name, slug=slug, district=district, province=province, city=district,
                                      latitude=28.2, longitude=84.0)


def _row(dest, daily, hotel=20, food=10, transport=5, local=2):
    return BudgetEstimation.objects.create(
        destination=dest, district=dest.district, province=dest.province, transport_cost=transport, food_cost_per_day=food,
        accommodation_per_night=hotel, local_transport=local, entry_fee=0, estimated_daily_budget=daily, estimated_trip_budget=daily * 3)


class RecordedBudgetFallbackTests(TestCase):
    def _post(self, dest):
        with ML_DOWN:
            return self.client.post("/api/v1/ml/budget/", {"destination": dest.id, "days": 3, "travelers": 2, "budget_level": "mid"},
                                    content_type="application/json")

    def test_own_row_is_used_and_labelled_destination(self):
        d = _dest("Bandipur", "bandipur", "Tanahun")
        _row(d, 80)
        body = self._post(d).json()
        self.assertEqual(body["source"], "dataset_csv")
        self.assertEqual(body["baseline_scope"], "destination")
        self.assertEqual(body["total_budget_usd"], 480.0)  # 80 * 3 days * 2 people

    def test_place_without_a_row_gets_the_labelled_district_median(self):
        a, b, target = _dest("A", "a", "Kaski"), _dest("B", "b", "Kaski"), _dest("Lakeside Viewpoint", "lv", "Kaski")
        _row(a, 60)
        _row(b, 100)
        body = self._post(target).json()
        self.assertEqual(body["baseline_scope"], "district")
        self.assertEqual(body["total_budget_usd"], 480.0)  # median 80 * 3 * 2
        self.assertIn("area baseline", body["living_costs_note"])

    def test_province_median_is_used_when_the_district_has_no_rows(self):
        a, target = _dest("A", "a", "Kaski"), _dest("Far Village", "fv", "Mustang")
        _row(a, 50)
        body = self._post(target).json()
        self.assertEqual(body["baseline_scope"], "province")

    def test_no_dataset_coverage_returns_fees_only_not_invented_costs(self):
        target = _dest("Nowhere", "nw", "Dolpa", province="Karnali")
        res = self._post(target)
        self.assertEqual(res.status_code, 200)
        body = res.json()
        self.assertTrue(body["official_fees_only"])
        self.assertIsNone(body["total_budget_usd"])
