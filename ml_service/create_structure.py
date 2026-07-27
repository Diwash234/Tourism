import csv
import json
import requests

# Fallback server endpoints in case the primary is down/blocking
ENDPOINTS = [
    "https://overpass.private.coffee/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://maps.mail.ru/osm/tools/overpass/api/interpreter",
]

# Query for tourism locations in Nepal
query = """
[out:json][timeout:180];
area["ISO3166-1"="NP"][admin_level=2]->.searchArea;
(
  node["tourism"](area.searchArea);
  way["tourism"](area.searchArea);
  relation["tourism"](area.searchArea);
);
out center;
"""

# Unique headers are required by OpenStreetMap policy
headers = {
    "User-Agent": "NepalTourismCSVApp/2.0 (contact: test@example.com)",
    "Accept": "application/json",
}

print("Fetching tourism data from OpenStreetMap for Nepal...")

response = None
for endpoint in ENDPOINTS:
    try:
        print(f"Trying server: {endpoint}")
        res = requests.post(
            endpoint, data={"data": query}, headers=headers, timeout=180
        )
        if res.status_code == 200:
            response = res
            print("Successfully connected and received data!")
            break
        else:
            print(f"Server replied with HTTP Status: {res.status_code}")
    except Exception as err:
        print(f"Could not connect to {endpoint}: {err}")

if response and response.status_code == 200:
    data = response.json()
    elements = data.get("elements", [])

    csv_filename = "nepal_tourism_destinations.csv"
    fields = [
        "ID",
        "Name",
        "Type",
        "Tourism_Category",
        "Latitude",
        "Longitude",
        "City",
    ]

    with open(
        csv_filename, mode="w", newline="", encoding="utf-8"
    ) as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=fields)
        writer.writeheader()

        for elem in elements:
            tags = elem.get("tags", {})
            lat = elem.get("lat") or elem.get("center", {}).get("lat")
            lon = elem.get("lon") or elem.get("center", {}).get("lon")

            writer.writerow(
                {
                    "ID": elem.get("id"),
                    "Name": tags.get("name", "N/A"),
                    "Type": elem.get("type"),
                    "Tourism_Category": tags.get("tourism", "N/A"),
                    "Latitude": lat,
                    "Longitude": lon,
                    "City": tags.get("addr:city", tags.get("address:city")),
                }
            )

    print(
        f"Done! Successfully created '{csv_filename}' with {len(elements)} items."
    )
else:
    print(
        "\nAll server attempts failed. Please check your internet connection or try again in a few minutes."
    )