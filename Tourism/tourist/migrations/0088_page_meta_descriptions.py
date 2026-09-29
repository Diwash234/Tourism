"""Replace auto-generated page descriptions ("<Title> on the Nepal Yatra").

Only rows whose description is still exactly the generated text (or the old
home-page slogan) are changed, so descriptions an editor wrote are kept.
Each replacement states what the page does; no rankings or claims.
"""
from django.db import migrations

DESCRIPTIONS = {
    "/": "Plan travel in Nepal: search destinations, compare places, build an itinerary, and check official entry rules, fees and emergency contacts.",
    "/about": "About Nepal Yatra and where its destination, hotel and safety information comes from.",
    "/budget-estimator": "Estimate a Nepal trip budget from official permit and park fees, recorded prices and live Nepal Rastra Bank exchange rates.",
    "/chatbot": "Ask questions about travel in Nepal and get answers based on the site's destination and safety records.",
    "/compare": "Compare up to four Nepal destinations side by side using the facts on record, with missing values clearly marked.",
    "/contact": "Contact the Nepal Yatra team about the site, your account, data corrections or privacy requests.",
    "/dashboard": "Your saved trips, favourites, booking requests and alerts on Nepal Yatra.",
    "/destinations": "Browse recorded destinations across Nepal's 77 districts by category, province and district, with sources for each record.",
    "/destinations/:slug": "Location, access, altitude, season, official fees, nearby services and emergency contacts for this Nepal destination.",
    "/destinations/submit": "Suggest a place in Nepal that is missing from the site. Submissions are reviewed before they are published.",
    "/discover-nepal": "Lesser-known Nepal destinations and published notices, drawn from the site's approved records.",
    "/emergency": "Nepal's national emergency numbers and the nearest recorded hospitals and police for each destination.",
    "/explore-map": "Explore Nepal's seven provinces and their districts on a map of recorded destinations.",
    "/family-safety": "Share your trip status with family and trusted contacts while you travel in Nepal.",
    "/favorites": "Destinations and places you have saved on Nepal Yatra.",
    "/footer": "Site footer content.",
    "/gallery": "Photographs of Nepal destinations, with their source where recorded.",
    "/history": "Places you have viewed or visited, visible only to you.",
    "/hotels": "Hotels and lodges on record across Nepal, verified listings first; unverified listings are labelled with their source.",
    "/itinerary": "Build a day-by-day Nepal itinerary from recorded places near your start point, with altitude and permit checks.",
    "/language": "Useful Nepali phrases for travellers, with pronunciation, and notes on languages spoken across Nepal.",
    "/my-bookings": "Your hotel, package and guide booking requests and their status.",
    "/navigation": "Routes between places in Nepal, labelled as road, corridor or straight-line so you know how each was measured.",
    "/packages": "Travel packages listed on Nepal Yatra, with what is included and how to request a booking.",
    "/recommendation": "Destination suggestions based on your interests, month and starting point, each with the reasons it was suggested.",
    "/risk-alerts": "Current weather and safety alerts for Nepal destinations, with the source and time of each alert.",
    "/settings": "Account, notification, language and privacy settings, including account deletion.",
    "/submit-service": "Register a tourism service in Nepal for review before it is listed.",
    "/translation": "Translate short phrases between Nepali, English and other languages for travel conversations.",
    "/trip-planner": "Plan a Nepal trip: choose places, days and budget, then save or share the plan.",
}

LEGACY_HOME = "Explore Nepal safely and intelligently."


def forwards(apps, schema_editor):
    ManagedPage = apps.get_model("tourist", "ManagedPage")
    for page in ManagedPage.objects.filter(route__in=DESCRIPTIONS.keys()):
        generated = f"{page.title} on the Nepal Yatra"
        if page.meta_description in (generated, LEGACY_HOME, ""):
            page.meta_description = DESCRIPTIONS[page.route][:320]
            page.save(update_fields=["meta_description"])


class Migration(migrations.Migration):
    dependencies = [("tourist", "0087_travel_plan_sharing")]
    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]
