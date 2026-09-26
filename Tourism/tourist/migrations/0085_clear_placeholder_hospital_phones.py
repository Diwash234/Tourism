"""Data hygiene for imported service records.

1. Blank templated placeholder phone numbers on unverified hospital records.

111 imported hospital rows carried numbers like "+977-037-520123" -- area code
plus a repeated "[4-6]x0123" template from the original project CSV, not real
numbers. Verified records are never touched.

2. Archive hospitals / health institutions that an early import filed into
the Hotel table (hospital names, or health-science institutions whose
"address" column holds a phone number). They are not
lodging and must not appear in hotel search. Archived, not deleted.
Medical-college hostels and "Hospitality" businesses are genuine lodging.
"""
import re

from django.db import migrations
from django.utils import timezone

_TEMPLATE_TAIL = re.compile(r"[4-6]\d0123$")


def _placeholder(value):
    text = str(value or "").strip()
    if text.endswith(".0"):
        text = text[:-2]
    digits = re.sub(r"\D", "", text)
    return len(digits) >= 8 and bool(_TEMPLATE_TAIL.search(digits))


def clear(apps, schema_editor):
    Hospital = apps.get_model("tourist", "Hospital")
    ids = [pk for pk, phone in Hospital.objects.filter(is_verified=False).values_list("pk", "phone") if _placeholder(phone)]
    Hospital.objects.filter(pk__in=ids).update(phone="")

    Hotel = apps.get_model("tourist", "Hotel")
    phone_like = re.compile(r"^\+?\d[\d\- ]{6,}$")
    hospital_name = re.compile(r"\bhospital\b", re.I)
    health_name = re.compile(r"health sciences?|medical", re.I)
    hostel = re.compile(r"hostel", re.I)

    def is_misfiled(name, address):
        name, address = name or "", (address or "").strip()
        if hostel.search(name):
            return False  # student hostels are genuine lodging
        if hospital_name.search(name):
            return True
        return bool(health_name.search(name) and phone_like.match(address))

    misfiled = [pk for pk, name, address in Hotel.objects.filter(is_active=True).values_list("pk", "name", "address")
                if is_misfiled(name, address)]
    Hotel.objects.filter(pk__in=misfiled).update(is_active=False, archived_at=timezone.now())


class Migration(migrations.Migration):
    dependencies = [("tourist", "0084_load_forex_seed_and_elevations")]
    operations = [migrations.RunPython(clear, migrations.RunPython.noop)]
