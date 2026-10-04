from unittest import mock

from django.core.cache import cache
from django.test import TestCase

from tourist.models import Destination, Hospital


class SharedPointDistanceTests(TestCase):
    """Directory rows imported from district lists share one town-centre point.
    Their distance is not metre-precise and must not be shown as if it were."""

    def setUp(self):
        cache.clear()  # nearby results are cached per destination id
        self.dest = Destination.objects.create(
            name="Rani Pokhari", slug="rani-pokhari", district="Kathmandu", city="Kathmandu",
            latitude=27.7060, longitude=85.3150)

    def _hospitals(self):
        with mock.patch("requests.post", side_effect=Exception("offline")), \
                mock.patch("requests.get", side_effect=Exception("offline")):
            res = self.client.get(f"/api/v1/destinations/{self.dest.id}/nearby-pois/?categories=hospitals")
        self.assertEqual(res.status_code, 200)
        return {r["name"]: r for r in res.json()["categories"]["hospitals"]["results"]}

    def test_rows_sharing_one_point_are_labelled_as_an_area_point(self):
        for n in ("Town Eye Hospital", "Town Nursing Home", "Town Medical College"):
            Hospital.objects.create(destination=self.dest, name=n, latitude=27.7100, longitude=85.3200)
        rows = self._hospitals()
        # Same-site duplicates collapse to one entry; whichever survives is flagged.
        self.assertEqual(len(rows), 1)
        row = next(iter(rows.values()))
        self.assertTrue(row["is_approximate"])
        self.assertIn("area point", row["distance_label"])

    def test_a_row_with_its_own_point_keeps_a_precise_label(self):
        Hospital.objects.create(destination=self.dest, name="Single Site Hospital", latitude=27.7080, longitude=85.3170)
        row = self._hospitals()["Single Site Hospital"]
        self.assertFalse(row["is_approximate"])
        self.assertNotIn("area point", row["distance_label"])

    def test_precise_rows_sort_before_approximate_ones(self):
        for n in ("A1", "A2", "A3"):
            Hospital.objects.create(destination=self.dest, name=n, latitude=27.7062, longitude=85.3152)  # nearest, but shared point
        Hospital.objects.create(destination=self.dest, name="Real Site", latitude=27.7100, longitude=85.3200)
        names = list(self._hospitals())
        self.assertEqual(names[0], "Real Site")
