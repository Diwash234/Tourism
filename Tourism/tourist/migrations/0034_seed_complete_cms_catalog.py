from django.db import migrations

PAGES = [
    ("home", "/", "Discover Nepal"), ("dashboard", "/dashboard", "Traveller Dashboard"),
    ("destinations", "/destinations", "Destinations"), ("gallery", "/gallery", "Visual Gallery"),
    ("compare", "/compare", "Compare Destinations"), ("discover-nepal", "/discover-nepal", "Discover Nepal"),
    ("packages", "/packages", "Travel Packages"), ("explore-map", "/explore-map", "Explore by Province"),
    ("recommendation", "/recommendation", "AI Recommendations"), ("navigation", "/navigation", "Route Navigation"),
    ("hotels", "/hotels", "Hotels and Lodges"), ("budget-estimator", "/budget-estimator", "Budget Estimator"),
    ("trip-planner", "/trip-planner", "Trip Planner"), ("itinerary", "/itinerary", "Itinerary Planner"),
    ("risk-alerts", "/risk-alerts", "Risk Alerts"), ("family-safety", "/family-safety", "Family Safety"),
    ("emergency", "/emergency", "Emergency Hub"), ("phrasebook", "/language", "Nepal Phrasebook"),
    ("translation", "/translation", "Live Translation"), ("chatbot", "/chatbot", "Himal AI Assistant"),
    ("favorites", "/favorites", "Saved Favorites"), ("bookings", "/my-bookings", "My Bookings"),
    ("history", "/history", "Visit History"), ("about", "/about", "About Us"),
    ("contact", "/contact", "Contact Us"), ("settings", "/settings", "Settings"),
    ("submit-place", "/destinations/submit", "Submit a Place"), ("submit-service", "/submit-service", "Submit a Tourism Service"),
]

NAV_GROUPS = [
    ("Explore", "/destinations", [("Destinations", "/destinations"), ("Gallery", "/gallery"), ("Compare Places", "/compare"), ("Explore by Province", "/explore-map")]),
    ("Plan", "/trip-planner", [("Trip Planner", "/trip-planner"), ("Itinerary", "/itinerary"), ("Budget Estimator", "/budget-estimator"), ("Hotels", "/hotels")]),
    ("Travel Safely", "/risk-alerts", [("Risk Alerts", "/risk-alerts"), ("Family Safety", "/family-safety"), ("Emergency", "/emergency")]),
]

SIDEBAR = [
    ("Destinations", "/destinations"), ("Visual Gallery", "/gallery"), ("Compare Places", "/compare"),
    ("Discover Nepal", "/discover-nepal"), ("Travel Packages", "/packages"), ("Submit Place", "/destinations/submit"),
    ("Submit Service", "/submit-service"), ("Explore by Province", "/explore-map"), ("AI Recommendations", "/recommendation"),
    ("Navigation", "/navigation"), ("Hotels & Lodges", "/hotels"), ("Budget Estimator", "/budget-estimator"),
    ("Trip Planner", "/trip-planner"), ("Itinerary Planner", "/itinerary"), ("Risk Alerts", "/risk-alerts"),
    ("Family Safety", "/family-safety"), ("Emergency Hub", "/emergency"), ("Phrasebook", "/language"),
    ("Live Translation", "/translation"), ("Himal AI Assistant", "/chatbot"), ("My Dashboard", "/dashboard"),
    ("Saved Favorites", "/favorites"), ("My Bookings", "/my-bookings"), ("Visit History", "/history"),
    ("Profile", "/profile"), ("Personal Details", "/personal-details"), ("My Submissions", "/my-submissions"),
    ("Admin Central", "/admin"), ("Diagnostics Center", "/admin/diagnostics"), ("Staff Operations", "/staff"),
    ("Local Guide Portal", "/local/dashboard"), ("Settings", "/settings"),
]

def seed(apps, schema_editor):
    Page=apps.get_model("tourist","ManagedPage");Section=apps.get_model("tourist","ContentSection");Nav=apps.get_model("tourist","ManagedNavigationItem")
    for order,(key,route,title) in enumerate(PAGES):
        page,_=Page.objects.get_or_create(key=key,defaults={"route":route,"title":title,"meta_description":f"{title} on the Digital Nepal Tourism Platform","status":"published","is_enabled":True})
        Section.objects.get_or_create(page=page,key="page-intro",defaults={"title":title,"subtitle":f"Explore {title.lower()} with verified tourism information.","body":"This section is managed from the Admin Content Publishing Studio.","display_order":0,"status":"published","is_visible":True})
        if key in {"home","destinations","dashboard","hotels","risk-alerts","emergency"}:
            Section.objects.get_or_create(page=page,key="featured-content",defaults={"title":f"Featured {title}","body":"Configure featured cards, media and calls to action here.","layout_variant":"cards","display_order":10,"status":"published","is_visible":True})
    for order,(label,route,children) in enumerate(NAV_GROUPS):
        parent,_=Nav.objects.get_or_create(location="navbar",label=label,defaults={"route":route,"display_order":order*10,"is_active":True})
        for child_order,(child_label,child_route) in enumerate(children):
            Nav.objects.get_or_create(location="navbar",label=child_label,parent=parent,defaults={"route":child_route,"display_order":child_order,"is_active":True})
    for order,(label,route) in enumerate(SIDEBAR):
        Nav.objects.get_or_create(location="sidebar",route=route,defaults={"label":label,"display_order":order,"is_active":True})

def reverse(apps,schema_editor):
    # Content is intentionally retained because administrators may have edited seeded records.
    pass

class Migration(migrations.Migration):
    dependencies=[("tourist","0033_hotel_archived_at_hotel_is_active_and_more")]
    operations=[migrations.RunPython(seed,reverse)]
