"""Diagnostic: media coverage and nearest-service attachment.

Aggregate-only: no per-row Python loops, so this stays fast on ~6.7k public
destinations.

Run: python manage.py shell < diag_media_links.py
"""
import sys

sys.stdout.reconfigure(encoding="utf-8")

from django.db.models import Count, Exists, OuterRef, Q  # noqa: E402

from tourist.models import (  # noqa: E402
    Destination,
    DestinationImage,
    Hospital,
    Hotel,
    PoliceStation,
)

PUBLIC_DEST = Q(status=Destination.SubmissionStatus.APPROVED, is_active=True)


def main():
    total = Destination.objects.filter(PUBLIC_DEST).count()
    print(f"public destinations            : {total}")

    # --- destination image coverage -------------------------------------
    # A DestinationImage the public serializers will actually serve:
    # approved + verified.
    approved_img = DestinationImage.objects.filter(
        destination_id=OuterRef("pk"),
        verification_status=DestinationImage.ImageStatus.APPROVED,
        is_verified=True,
    )
    with_img = Destination.objects.filter(PUBLIC_DEST).filter(
        Exists(approved_img)
    ).count()
    print(f"  with >=1 APPROVED+verified img: {with_img}")
    print(f"  with NO approved image       : {total - with_img}")

    no_cover_col = Destination.objects.filter(PUBLIC_DEST).filter(
        Q(cover_image__isnull=True) | Q(cover_image="")
    ).count()
    print(f"  cover_image column empty     : {no_cover_col}")

    # --- hotel image coverage -------------------------------------------
    hotels = Hotel.objects.filter(is_active=True)
    h_total = hotels.count()
    h_no = hotels.filter(
        Q(cover_image__isnull=True) | Q(cover_image="")
    ).exclude(external_image_url__isnull=False).exclude(external_image_url="").count()
    print(f"active hotels                  : {h_total}")
    print(f"  hotels with no image at all  : {h_no}")

    # --- hospital image coverage ----------------------------------------
    hos_total = Hospital.objects.count()
    hos_no = Hospital.objects.filter(Q(image__isnull=True) | Q(image="")).count()
    print(f"hospitals                      : {hos_total}")
    print(f"  hospitals with no image      : {hos_no}")

    # --- nearest-service attachment -------------------------------------
    pub_ids = Destination.objects.filter(PUBLIC_DEST).values("id")
    hosp_attached = (
        Hospital.objects.filter(destination__in=pub_ids)
        .values("destination_id")
        .distinct()
        .count()
    )
    hotel_attached = (
        Hotel.objects.filter(destination__in=pub_ids, is_active=True)
        .values("destination_id")
        .distinct()
        .count()
    )
    police_attached = (
        PoliceStation.objects.filter(destination__in=pub_ids)
        .values("destination_id")
        .distinct()
        .count()
    )
    print(f"dests with >=1 hospital        : {hosp_attached} / {total}")
    print(f"dests with >=1 active hotel    : {hotel_attached} / {total}")
    print(f"dests with >=1 police station  : {police_attached} / {total}")

    orphan_hospital = Hospital.objects.filter(destination__isnull=True).count()
    orphan_police = PoliceStation.objects.filter(destination__isnull=True).count()
    orphan_hotel = Hotel.objects.filter(destination__isnull=True).count()
    print(f"hospitals with NO destination  : {orphan_hospital}")
    print(f"police with NO destination     : {orphan_police}")
    print(f"hotels with NO destination     : {orphan_hotel}")

    # --- coverage by district: where are the gaps? ----------------------
    print("\nper-district hospital coverage (top 15 districts by public dests):")
    rows = (
        Destination.objects.filter(PUBLIC_DEST)
        .exclude(district__isnull=True)
        .exclude(district="")
        .values("district")
        .annotate(
            n=Count("id"),
            with_hosp=Count(
                "id",
                filter=Exists(
                    Hospital.objects.filter(destination_id=OuterRef("id"))
                ),
            ),
        )
        .order_by("-n")[:15]
    )
    for r in rows:
        print(f"   {r['district'][:28]:<28} dests={r['n']:>4}  with_hospital={r['with_hosp']:>4}")

    # --- duplicate / junk image urls ------------------------------------
    print("\nimage source distribution (top 10):")
    for r in (
        DestinationImage.objects.values("source")
        .annotate(n=Count("id"))
        .order_by("-n")[:10]
    ):
        print(f"   {str(r['source']):<22} {r['n']}")


main()