import json
import urllib.request


def post(days, city="Pokhara"):
    body = json.dumps({
        "start_city": city,
        "days": days,
        "travelers": 2,
        "budget_level": "mid",
    }).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8000/api/v1/ml/itinerary/",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    return json.load(urllib.request.urlopen(req, timeout=40))


for n in [1, 3, 7, 15, 20, 30]:
    d = post(n)
    got = len(d.get("itinerary", []))
    print("requested=%2d -> returned_days=%2d  days_field=%s  title=%s"
          % (n, got, d.get("days"), d.get("title")))

print()
d = post(20, "Pokhara")
for row in d["itinerary"][14:]:
    print("  day", row["day"], "|", row["summary"][:88])
print()
print("nearest_hotel_info :", d.get("nearest_hotel_info"))
print("nearest_hospital_info:", d.get("nearest_hospital_info"))
print("images:", len(d.get("images") or []))