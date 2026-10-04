"""A destination must never show another place's photograph, and itineraries
must be made of places to visit rather than hotels or other businesses."""
from django.test import TestCase

from tourist.models import Destination, DestinationImage
from tourist.serializers import destination_cover_image, _overshared_image_urls, _OVERSHARED_CACHE

WM = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/{}/960px-{}"


def wm(title):
    return WM.format(title, title)


class CoverMatchesPlaceTests(TestCase):
    def assertNotPhoto(self, destination):
        """A rejected photo must fall back to the generated postcard (the site
        no longer shows a broken "image unavailable" card), never to the wrong
        place's photograph."""
        url = destination_cover_image(destination)
        self.assertTrue(
            url is None or str(url).startswith("/api/v1/postcard/"),
            f"expected no photo / generated postcard, got {url}",
        )
        self.assertNotEqual(url, destination.cover_image)

    def setUp(self):
        _OVERSHARED_CACHE.update(at=0.0, urls=frozenset())

    def _dest(self, name, slug, cover, district="Kathmandu"):
        return Destination.objects.create(name=name, slug=slug, cover_image=cover, district=district, city=district)

    def test_cover_naming_the_place_is_kept(self):
        d = self._dest("Boudhanath Stupa", "boud", wm("Boudhanath_Stupa_Kathmandu_Nepal.jpg"))
        self.assertEqual(destination_cover_image(d), d.cover_image)

    def test_cover_of_a_different_place_is_rejected(self):
        d = self._dest("Mahaboudha Temple", "maha", wm("Boudhanath_Stupa_Kathmandu_Nepal.jpg"))
        self.assertNotPhoto(d)

    def test_city_name_in_title_does_not_count_as_a_match(self):
        d = self._dest("Hotel Elite", "elite", wm("SAARC_Secretariat_at_Kathmandu.JPG"))
        self.assertNotPhoto(d)

    def test_opaque_photo_reused_by_three_places_is_rejected(self):
        url = "https://live.staticflickr.com/65535/321679d01426026a3_k.jpg"
        ds = [self._dest(f"Village {i}", f"v{i}", url, district="Gorkha") for i in range(3)]
        self.assertNotPhoto(ds[0])

    def test_opaque_photo_used_once_is_kept(self):
        d = self._dest("Barpak", "barpak", "https://live.staticflickr.com/65535/unique_k.jpg", district="Gorkha")
        self.assertEqual(destination_cover_image(d), d.cover_image)

    def test_staff_chosen_gallery_photo_overrides_the_filename_heuristic(self):
        from tourist.models import User
        staff = User.objects.create_superuser("cover-staff@test.local", "Sup!Pass123")
        url = "https://cdn.example.com/Boudhanath_Stupa_Kathmandu_Nepal.jpg"
        d = self._dest("Mahaboudha Temple", "maha2", url)
        DestinationImage.objects.create(
            destination=d, external_url=url, verification_status="approved", is_verified=True,
            source=DestinationImage.Source.ADMIN, uploaded_by=staff)
        self.assertEqual(destination_cover_image(d), url)

    def test_hotel_does_not_borrow_the_landmark_photo_of_its_city(self):
        d = self._dest("Lumbini Garden Lodge", "llodge", wm("Lumbini_Sacred_Garden-118029.jpg"), district="Rupandehi")
        self.assertNotPhoto(d)

    def test_camera_style_filename_is_neutral_and_stays_visible(self):
        """Upstream #22: generic source filenames (IMG_2041.jpg) are real photos and must show."""
        d = self._dest("Barpak", "barpak-img", wm("IMG_2041.jpg"), district="Gorkha")
        self.assertEqual(destination_cover_image(d), d.cover_image)

    def test_named_photo_of_another_town_is_rejected_for_a_hostel(self):
        d = self._dest("PG girls hostel", "pgh", wm("Kirtipur%2C_1950_-_1955.jpg"), district="Kathmandu")
        self.assertNotPhoto(d)

    def test_real_landmark_keeps_its_own_photo(self):
        d = self._dest("Lumbini Sacred Garden", "lsg", wm("Lumbini_Sacred_Garden-118029.jpg"), district="Rupandehi")
        self.assertEqual(destination_cover_image(d), d.cover_image)
