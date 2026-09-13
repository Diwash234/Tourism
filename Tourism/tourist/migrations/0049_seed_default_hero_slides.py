"""Seed the cinematic landing hero with six authentic Himalayan slides.

Idempotent: uses get_or_create keyed on ``title`` so re-running never
duplicates. Reverse removes exactly the seeded titles. Uses bundled
``/images/...`` assets so slides render even with no uploads or network.
"""
from django.db import migrations

SLIDES = [
    dict(order=1, title="EVEREST", kicker="Solukhumbu · Altitude 8,849 m",
         subtitle="Everest Base Camp & Khumbu Peaks",
         tagline="Journey into the heart of the Himalayas at the roof of the world.",
         link_slug="everest-base-camp", local_image="/images/destinations/everest/base-camp.jpg",
         overlay_strength=62, focal_point="top", duration_seconds=7),
    dict(order=2, title="ANNAPURNA", kicker="Kaski · 4,130 m",
         subtitle="Alpine Sanctuary & Rhododendron Trails",
         tagline="Glacier amphitheatres and Gurung heritage villages beneath Machhapuchhre.",
         link_slug="annapurna-base-camp", local_image="/images/destinations/annapurna/trek.jpg",
         overlay_strength=60, focal_point="center", duration_seconds=7),
    dict(order=3, title="MUSTANG", kicker="Mustang · 3,840 m",
         subtitle="Lo Manthang Walled Kingdom",
         tagline="Rain-shadow desert canyons, ancient cliff caves and Tibetan culture.",
         link_slug="lo-manthang", local_image="/images/destinations/mustang/lo-manthang.jpg",
         overlay_strength=60, focal_point="center", duration_seconds=7),
    dict(order=4, title="POKHARA", kicker="Kaski · Lakeside",
         subtitle="Phewa Lake & the Annapurna Skyline",
         tagline="Lakeside calm mirrored beneath the fish-tail peak of Machhapuchhre.",
         link_slug="phewa-lake", local_image="/images/destinations/pokhara/fewatal.jpg",
         overlay_strength=58, focal_point="bottom", duration_seconds=7),
    dict(order=5, title="LANGTANG", kicker="Langtang · Valley of Glaciers",
         subtitle="Tamang Villages beneath Langtang Lirung",
         tagline="The nearest Himalayan valley — pine forest, yaks and glacier viewpoints.",
         link_slug="langtang-valley-trek", local_image="/images/destinations/langtang/valley.jpg",
         overlay_strength=60, focal_point="center", duration_seconds=7),
    dict(order=6, title="RARA", kicker="Mugu · 2,990 m",
         subtitle="Queen of Lakes in Wild West Nepal",
         tagline="Crystal alpine waters ringed by pine forests in remote Karnali.",
         link_slug="rara-lake", local_image="/images/destinations/rara/alpine-lake.jpg",
         overlay_strength=56, focal_point="center", duration_seconds=7),
]


def seed(apps, schema_editor):
    HeroSlide = apps.get_model("tourist", "HeroSlide")
    for slide in SLIDES:
        HeroSlide.objects.get_or_create(title=slide["title"], defaults=slide)


def unseed(apps, schema_editor):
    HeroSlide = apps.get_model("tourist", "HeroSlide")
    HeroSlide.objects.filter(title__in=[s["title"] for s in SLIDES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0048_heroslide"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
