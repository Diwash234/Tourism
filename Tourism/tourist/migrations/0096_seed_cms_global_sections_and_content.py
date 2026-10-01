from django.db import migrations

GLOBAL_SECTIONS = [
    (
        "topbar",
        {
            "enabled": True,
            "status": "published",
            "helpline": "1144 / +977-1-4247041",
            "emergency_label": "24/7 Tourist Police Hotline",
            "notice": "Autumn 2026 Trekking Season Open · Favorable weather across Annapurna & Everest circuits",
            "weather_summary": "Kathmandu 21°C · Pokhara 23°C · Namche 9°C",
            "emergency_url": "/emergency",
            "show_language": True,
            "apply_button_label": "Apply Now",
            "apply_button_action": "open_modal",
        },
        "Global Topbar settings: hotline, announcements, weather ticker, emergency CTA",
    ),
    (
        "global_navbar",
        {
            "status": "published",
            "logo_text": "Nepal Yatra",
            "logo_tagline": "Discover the Himalayas",
            "show_search": True,
            "show_weather": True,
            "show_theme_toggle": True,
            "cta_label": "Apply / Inquire",
            "cta_action": "open_modal",
            "cta_url": "/packages",
        },
        "Global Header & Navbar settings: brand copy, search visibility, quick action CTA",
    ),
    (
        "footer",
        {
            "status": "published",
            "brand_name": "Nepal Yatra",
            "brand_description": "Nepal's authoritative, verified tourism portal. Live trail conditions, authentic cultural destinations, vetted local guides and mountain safety dispatch.",
            "helpline_text": "Emergency Dispatch: 1144 (Tourist Police) · 100 (Nepal Police) · 102 (Ambulance)",
            "copyright": "© 2026 Nepal Yatra Tourism Board. Government of Nepal. All rights reserved.",
            "show_newsletter": True,
            "newsletter_title": "Stay Connected with the Himalayas",
            "newsletter_subtitle": "Receive monthly seasonal guides, weather advisories and trail updates.",
            "social_links": {
                "facebook": "https://facebook.com",
                "instagram": "https://instagram.com",
                "youtube": "https://youtube.com",
                "twitter": "https://twitter.com",
            },
        },
        "Global Footer settings: brand description, emergency contacts, legal copyright, social channels",
    ),
    (
        "cta_banners",
        {
            "enabled": True,
            "status": "published",
            "badge": "Autumn 2026 Season",
            "title": "Experience Nepal Beyond the Beaten Path",
            "subtitle": "Discover 6,700+ verified destinations, certified mountain guides, and real-time safety tracking across all 7 provinces.",
            "button_text": "Plan Your Expedition",
            "button_url": "/itinerary",
            "secondary_text": "Emergency Hub",
            "secondary_url": "/emergency",
            "theme": "emerald",
        },
        "Global Call-to-Action banner displayed across public pages",
    ),
    (
        "action_buttons",
        {
            "enabled": True,
            "status": "published",
            "primary_label": "Apply / Inquire Now",
            "primary_action": "open_modal",
            "primary_url": "/trip",
            "secondary_label": "Find Verified Guides",
            "secondary_url": "/guides",
            "floating_sos": True,
        },
        "Global Apply & Quick Action buttons",
    ),
    (
        "tickers",
        {
            "enabled": True,
            "status": "published",
            "speed": "normal",
            "items": [
                "Kathmandu Valley Heritage Festival: Sep 25 – Oct 15, 2026",
                "Annapurna Circuit Route Status: Clear & Open for Autumn Treks",
                "Everest Base Camp Weather: Favorable high visibility conditions",
                "24/7 Tourist Police Helpline: Dial 1144 for nationwide tourist assistance",
                "Foreign Exchange Rates updated daily · Visa on Arrival available at TIA",
            ],
        },
        "Live animated marquee ticker with breaking travel advisories and route alerts",
    ),
    (
        "chat_widget",
        {
            "enabled": True,
            "status": "published",
            "title": "Himal AI Assistant",
            "subtitle": "Your Nepal Travel Companion",
            "greeting": "Namaste! I am Himal, your Nepal travel companion. How may I assist your Himalayan journey today?",
            "quick_prompts": [
                "What is the best trek for beginners?",
                "Annapurna Circuit permit requirements",
                "How to reach Pokhara from Kathmandu?",
                "Emergency numbers and tourist police",
            ],
            "primary_color": "#0B3D91",
        },
        "Himal AI Chat Widget appearance and greeting configuration",
    ),
    (
        "admission_modal",
        {
            "enabled": True,
            "status": "published",
            "title": "Nepal Journey Inquiry & Booking Request",
            "subtitle": "Tell us your travel plans. Our verified tourism coordinators will assist you with permits, vetted guides and tailored itineraries.",
            "button_label": "Submit Travel Inquiry",
            "success_message": "Thank you! Your travel inquiry has been received. Our team will contact you within 24 hours.",
        },
        "Travel Inquiry & Admission Request modal popup configuration",
    ),
]

CONTENT_COLLECTIONS = [
    (
        "cms_content_news",
        [
            {"id": 1, "title": "Autumn 2026 Trekking Season Officially Opened by Ministry", "category": "Official Notice", "date": "2026-09-15", "author": "Nepal Tourism Board", "status": "published", "summary": "The Ministry of Culture, Tourism and Civil Aviation announced full route clearance for Everest, Annapurna, and Langtang."},
            {"id": 2, "title": "Annapurna Conservation Area Launches Digital Smart Passes", "category": "Conservation", "date": "2026-09-10", "author": "ACAP Project", "status": "published", "summary": "Trekkers can now verify ACAP permits via mobile QR codes at Besisahar and Nayapul checkpoints."},
            {"id": 3, "title": "Pokhara International Airport Adds Direct Regional Flights", "category": "Aviation", "date": "2026-09-02", "author": "Civil Aviation Authority", "status": "published", "summary": "New scheduled routes connecting Pokhara with Varanasi and Chengdu commence this autumn."},
            {"id": 4, "title": "Chitwan National Park Welcomes Newborn Greater One-Horned Rhino", "category": "Wildlife", "date": "2026-08-28", "author": "Department of National Parks", "status": "published", "summary": "Park rangers recorded the healthy calf in the Sauraha buffer zone during the late monsoon census."},
            {"id": 5, "title": "High Altitude Health Station Upgrades in Pheriche & Dingboche", "category": "Safety", "date": "2026-08-20", "author": "Himalayan Rescue Association", "status": "published", "summary": "New hyperbaric chambers and telemedicine satellite links installed for high-altitude trekkers."},
            {"id": 6, "title": "Nepal Yatra Launches Real-Time Mountain Weather Alert System", "category": "Technology", "date": "2026-08-14", "author": "Nepal Yatra Dev Team", "status": "published", "summary": "Meteorological sensors on major passes now stream live hourly wind and precipitation data."},
            {"id": 7, "title": "Kathmandu Heritage Walk Restorations Completed Ahead of Indra Jatra", "category": "Culture", "date": "2026-08-05", "author": "Department of Archaeology", "status": "published", "summary": "Restored historic monuments and traditional paving open across Asan, Indrachowk, and Basantapur."},
            {"id": 8, "title": "Langtang Valley Eco-Trail Receives Sustainable Tourism Award", "category": "Ecotourism", "date": "2026-07-28", "author": "Global Travel Forum", "status": "published", "summary": "Community-led waste management and solar heating initiatives recognized internationally."},
            {"id": 9, "title": "Rara Lake Eco-Lodge Project Commences Construction in Karnali", "category": "Development", "date": "2026-07-15", "author": "Karnali Province Tourism", "status": "published", "summary": "Eco-friendly wooden lodges designed to blend with Rara National Park pine forests."},
            {"id": 10, "title": "New Trekking Route Mapped in Western Dhaulagiri Circuit", "category": "Exploration", "date": "2026-06-30", "author": "Trekking Agencies Association", "status": "published", "summary": "Pristine ridge trail offers panoramic views of Dhaulagiri I-V and untouched Gurung villages."},
            {"id": 11, "title": "Mountaineering Association Publishes 2026 Peak Permit Guidelines", "category": "Mountaineering", "date": "2026-06-18", "author": "Nepal Mountaineering Association", "status": "published", "summary": "Updated environmental deposit and waste repatriation protocols for 6,000m trekking peaks."},
            {"id": 12, "title": "Himalayan Solar Microgrid Powering Solukhumbu Sherpa Villages", "category": "Sustainability", "date": "2026-06-01", "author": "Clean Energy Nepal", "status": "published", "summary": "Clean, reliable renewable energy reaches Khumjung and Thame teahouse networks."},
        ],
        "Official Nepal Tourism News & Press Releases (12 items)",
    ),
    (
        "cms_content_blogs",
        [
            {"id": 1, "title": "My 14-Day Journey Along the Annapurna Circuit as a University Student", "author": "Aayush Sharma", "date": "2026-09-12", "status": "published", "tags": "Trekking, Student Travel, Budget", "summary": "Practical tips on teahouse budgeting, crossing Thorong La at sunrise, and packing light."},
            {"id": 2, "title": "Field Notes from Rara: Reflections on Karnali's Remote Beauty", "author": "Pooja Gurung", "date": "2026-08-19", "status": "published", "tags": "Karnali, Lake Rara, Culture", "summary": "A peaceful journey through Jumla's apple orchards and the crystalline blue waters of Rara Lake."},
        ],
        "Traveler & Student Field Blogs (2 items)",
    ),
    (
        "cms_content_notices",
        [
            {"id": 1, "title": "TIMS Card Verification at All Trek Entry Points", "level": "warning", "date": "2026-09-01", "status": "published", "summary": "Mandatory guide requirement active for foreign solo trekkers in designated national parks."},
            {"id": 2, "title": "Tourist Police 24/7 Helpline: Dial 1144", "level": "info", "date": "2026-08-01", "status": "published", "summary": "Multilingual assistance available for emergency dispatch, lost belongings, and road queries."},
            {"id": 3, "title": "Sagarmatha Single-Use Plastic Prohibition", "level": "danger", "date": "2026-07-15", "status": "published", "summary": "Fines applicable for disposable beverage bottles and non-biodegradable wrappers in Solukhumbu."},
            {"id": 4, "title": "Prithvi Highway Monsoon Maintenance Advisory", "level": "warning", "date": "2026-08-10", "status": "published", "summary": "Intermittent lane restrictions near Mugling for hillside slope stabilization."},
            {"id": 5, "title": "Drone Flying Permit Protocols", "level": "info", "date": "2026-06-01", "status": "published", "summary": "Civil Aviation Authority authorization required prior to aerial filming near heritage sites."},
            {"id": 6, "title": "Autumn Visa on Arrival Operational at TIA", "level": "info", "date": "2026-09-01", "status": "published", "summary": "Online visa pre-registration recommended to avoid queues at immigration counters."},
            {"id": 7, "title": "Altitude Acclimatization Guidelines for 3,000m+", "level": "warning", "date": "2026-09-05", "status": "published", "summary": "Never ascend more than 500m net elevation gain per day above Namche or Manang."},
            {"id": 8, "title": "Manaslu Restricted Area Group Size Requirements", "level": "info", "date": "2026-08-25", "status": "published", "summary": "Minimum two trekkers plus licensed guide mandatory for special immigration permits."},
            {"id": 9, "title": "Upper Mustang Tiji Festival Booking Dates", "level": "info", "date": "2026-05-10", "status": "published", "summary": "Advance accommodation booking advised for Lo Manthang cultural festival periods."},
            {"id": 10, "title": "Bespoke Guide Verification Badge Verification", "level": "info", "date": "2026-07-20", "status": "published", "summary": "Verify certified guide IDs through the Nepal Yatra portal prior to booking."},
            {"id": 11, "title": "Kathmandu Valley Dashain Public Transport Timetable", "level": "info", "date": "2026-09-20", "status": "published", "summary": "Adjusted inter-city bus departures from Gongabu New Bus Park during festival week."},
            {"id": 12, "title": "Langtang Gosaikunda Holy Lake Clean-Up Drive", "level": "info", "date": "2026-08-15", "status": "published", "summary": "Volunteers and park wardens collect bio-waste following Janai Purnima pilgrimage."},
            {"id": 13, "title": "Wildlife Safety Protocol in Bardia & Chitwan", "level": "warning", "date": "2026-07-05", "status": "published", "summary": "Do not wander outside resort boundaries after dusk without an accompanying nature guide."},
            {"id": 14, "title": "Foreign Exchange Counter Locations & Regulations", "level": "info", "date": "2026-08-01", "status": "published", "summary": "Nepal Rastra Bank certified currency exchange booths active across Thamel and Lakeside."},
            {"id": 15, "title": "Helicopter Evacuation Fraud Prevention Measures", "level": "danger", "date": "2026-09-01", "status": "published", "summary": "Only use authorized dispatch coordination through tourist police and verified insurers."},
            {"id": 16, "title": "Shey Phoksundo National Park Yarsagumba Harvest Closure", "level": "info", "date": "2026-06-30", "status": "published", "summary": "High alpine meadows re-opened for regular trekking after annual harvesting window."},
            {"id": 17, "title": "Tribhuvan International Airport Runway Maintenance Completed", "level": "info", "date": "2026-08-30", "status": "published", "summary": "Full 24-hour flight operations restored following routine scheduled resurfacing."},
            {"id": 18, "title": "Lumbini Sacred Garden Silence & Respect Zone", "level": "info", "date": "2026-07-10", "status": "published", "summary": "Designated meditation zones and shoe-free walkways around Mayadevi Temple."},
            {"id": 19, "title": "Emergency SOS Location Sharing via Nepal Yatra App", "level": "info", "date": "2026-09-18", "status": "published", "summary": "Download offline emergency cards and register trusted emergency contacts before trekking."},
        ],
        "Official Notices and Travel Advisories (19 items)",
    ),
    (
        "cms_content_results",
        [
            {"id": 1, "title": "2026 Top Rated Trekking Trails of Nepal", "metric": "98.4% Satisfaction", "category": "Trekking", "status": "published", "summary": "Annapurna Circuit and Manaslu rated highest for cultural interaction and trail hospitality."},
            {"id": 2, "title": "Traveler Choice: Best Cultural Homestay Awards", "metric": "Top 10 Homestays", "category": "Hospitality", "status": "published", "summary": "Ghandruk, Panauti, and Sirubari recognized for authentic culinary and cultural immersion."},
            {"id": 3, "title": "Clean Trail Initiative Annual Rankings", "metric": "94% Cleanliness Score", "category": "Environment", "status": "published", "summary": "Langtang Valley ranked cleanest trekking corridor with zero landfill waste exports."},
            {"id": 4, "title": "Nepal Mountain Photography Competition 2026", "metric": "1,200 Submissions", "category": "Arts", "status": "published", "summary": "Winning photographs showcased in Nepal Yatra digital gallery and national exhibition."},
            {"id": 5, "title": "Hospitality Excellence Standards Report", "metric": "2,700 Verified Hotels", "category": "Standards", "status": "published", "summary": "Annual hygiene, safety, and digital pricing audit results published across all 7 provinces."},
        ],
        "Rankings, Benchmark Results and Tourism Awards (5 items)",
    ),
    (
        "cms_content_events",
        [
            {"id": 1, "title": "Indra Jatra & Kathmandu Cultural Expo 2026", "date": "2026-09-24", "location": "Kathmandu Durbar Square", "status": "published", "summary": "Traditional masked dances, chariot processions of Living Goddess Kumari, and cultural fairs."},
            {"id": 2, "title": "Himalayan Wilderness First Aid & Mountain Safety Workshop", "date": "2026-10-05", "location": "Pokhara Adventure Hub", "status": "published", "summary": "Intensive hands-on training for licensed guides and high-altitude trekking expedition leaders."},
            {"id": 3, "title": "Pokhara Paragliding & Adventure Tourism Meet", "date": "2026-10-18", "location": "Sarangkot, Pokhara", "status": "published", "summary": "International aerial sports exhibition celebrating scenic Sarangkot launch points."},
            {"id": 4, "title": "International Mountain Day 2026 Symposium", "date": "2026-12-11", "location": "Nepal Academy, Kamaladi", "status": "published", "summary": "High-level policy dialogue on climate resilience, glacier monitoring, and sherpa community welfare."},
        ],
        "Events, Cultural Festivals & Mountain Workshops (4 items)",
    ),
    (
        "cms_content_programs",
        [
            {"id": 1, "title": "Great Himalayan Trail Expedition Series", "duration": "30-150 Days", "difficulty": "Challenging", "status": "published", "summary": "Traversing the highest mountain pass network in the world from Kanchenjunga to Humla."},
            {"id": 2, "title": "Community Homestay & Cultural Immersion Program", "duration": "7-14 Days", "difficulty": "Moderate", "status": "published", "summary": "Connecting travellers directly with indigenous Newari, Tamang, Tharu, and Gurung families."},
            {"id": 3, "title": "Youth Mountain Ecology & Leadership Trek", "duration": "10 Days", "difficulty": "Moderate", "status": "published", "summary": "Educational field study examining glacial retreat and sub-alpine biodiversity in Langtang."},
        ],
        "Signature Tourism & Trekking Programs (3 items)",
    ),
    (
        "cms_content_scholarships",
        [
            {"id": 1, "title": "Nepal Tourism Board High-Altitude Guide Training & Porter Welfare Grant", "beneficiaries": "120 Porters & Junior Guides", "value": "NPR 5,000,000 Total Fund", "status": "published", "summary": "Tuition waivers and cold-weather mountain gear subsidies for aspiring Sherpa and Rai guides."},
        ],
        "Scholarships, Welfare Grants & Sustainable Funds (1 item)",
    ),
    (
        "cms_content_faqs",
        [
            {"id": 1, "question": "Do I need a TIMS card and National Park permit?", "answer": "Yes. Trekkers in all protected conservation areas require a TIMS (Trekkers' Information Management System) card and the relevant national park entry permit (such as ACAP for Annapurna or SNP for Sagarmatha).", "category": "Permits", "status": "published"},
            {"id": 2, "question": "What is the best season to trek in Nepal?", "answer": "Autumn (September to November) offers the clearest mountain views and stable weather. Spring (March to May) features blooming rhododendrons and warmer conditions.", "category": "Seasons", "status": "published"},
            {"id": 3, "question": "How does the emergency SOS dispatch work on Nepal Yatra?", "answer": "Clicking SOS in the emergency hub triggers your real GPS coordinates to the Tourist Police central control room (Hotline 1144) and alerts your saved trusted contacts.", "category": "Safety", "status": "published"},
            {"id": 4, "question": "Can I convert foreign currencies at regional hubs?", "answer": "Major international currencies (USD, EUR, GBP) are accepted at banks and licensed exchange counters in Kathmandu and Pokhara. In mountain teahouses, only Nepali Rupees (NPR) in cash are accepted.", "category": "Money", "status": "published"},
        ],
        "Frequently Asked Questions (4 items)",
    ),
    (
        "cms_content_applications",
        [
            {"id": 1, "applicant_name": "Tashi Dorje Sherpa", "type": "Certified Local Guide", "experience_years": 8, "status": "pending_review", "date": "2026-09-18", "summary": "Sagarmatha and Rolwaling circuit trekking guide certification application with NMA credentials."},
        ],
        "Guide and Tourism Partner Applications (1 item)",
    ),
    (
        "cms_content_enquiries",
        [],
        "Inbound Traveler Enquiries and Itinerary Requests",
    ),
    (
        "cms_content_feedback",
        [
            {"id": 1, "user_name": "Elena Rostova", "country": "Sweden", "rating": 5, "date": "2026-09-14", "status": "published", "comment": "The live route alerts and accurate elevation profiles saved us when planning our Manaslu trek."},
        ],
        "Traveler Feedback & Ratings (1 item)",
    ),
    (
        "cms_content_testimonials",
        [
            {"id": 1, "author": "David & Sarah Linwood", "origin": "Edinburgh, UK", "trek": "Everest Base Camp & Gokyo Lakes", "rating": 5, "quote": "Nepal Yatra made every step of our journey transparent, vetted and reliable. Having 24/7 hotline support gave us total peace of mind.", "status": "published"},
        ],
        "Verified Traveler Testimonials (1 item)",
    ),
    (
        "cms_content_surveys",
        [
            {"id": 1, "title": "Annual Nepal Visitor Experience & Trail Safety Survey 2026", "responses_count": 3, "status": "published", "questions": ["How was your teahouse cleanliness?", "Were trail markers clear?", "Did you feel safe?"]},
        ],
        "Visitor Questionnaires and Safety Surveys (1 item)",
    ),
    (
        "cms_content_survey_responses",
        [
            {"id": 1, "survey_id": 1, "respondent": "Anonymous (Trekker #409)", "route": "Annapurna Circuit", "satisfaction": "Exceptional", "date": "2026-09-16", "recommendation": "10/10"},
            {"id": 2, "survey_id": 1, "respondent": "Anonymous (Trekker #410)", "route": "Langtang Valley", "satisfaction": "Very Good", "date": "2026-09-18", "recommendation": "9/10"},
            {"id": 3, "survey_id": 1, "respondent": "Anonymous (Trekker #411)", "route": "Mardi Himal", "satisfaction": "Exceptional", "date": "2026-09-20", "recommendation": "10/10"},
        ],
        "Submitted Survey Responses (3 items)",
    ),
    (
        "cms_content_abstracts",
        [
            {"id": 1, "title": "Ecological Resilience of Sub-Alpine Flora in Sagarmatha National Park", "author": "Dr. Pradeep Bhattarai et al.", "institution": "Tribhuvan University, Institute of Science", "date": "2026-07", "status": "published", "abstract": "Investigating high-altitude vegetation recovery and climate-induced treeline shifts along the Khumbu Valley."},
            {"id": 2, "title": "Socio-Economic Impacts of Ecotourism in Ghandruk and Upper Mustang", "author": "Dr. Maya Shrestha", "institution": "Kathmandu University Department of Development Studies", "date": "2026-05", "status": "published", "abstract": "Comparative assessment of community-managed homestay revenues and heritage preservation incentives."},
            {"id": 3, "title": "Acute Mountain Sickness: Incidence and Mitigation Strategies along Thorong La", "author": "Dr. Buddha Basnyat et al.", "institution": "Himalayan Rescue Association Research Division", "date": "2026-04", "status": "published", "abstract": "Prospective cohort analysis of 1,400 trekkers ascending above 5,000m with pulse oximetry tracking."},
            {"id": 4, "title": "Geomorphological Hazard Mapping along the Manaslu Circuit", "author": "Er. Suman Adhikari", "institution": "Department of Mines and Geology", "date": "2026-03", "status": "published", "abstract": "LiDAR and satellite interferometry for real-time rockfall and landslide early warning systems."},
            {"id": 5, "title": "Indigenous Architectural Conservation in Patan and Bhaktapur", "author": "Prof. Rabindra Puri", "institution": "Nepal Heritage Foundation", "date": "2026-01", "status": "published", "abstract": "Traditional timber joinery, dachi appa brickwork, and seismic retrofitting of Newari monuments."},
        ],
        "Research Abstracts on Himalayan Ecology, Medicine and Heritage (5 items)",
    ),
    (
        "cms_content_journals",
        [
            {"id": 1, "title": "Himalayan Journal of Sustainable Tourism (Vol 14, Issue 2)", "editor": "Nepal Tourism Board Research Cell", "year": "2026", "status": "published", "pages": 148, "issn": "2392-4829"},
            {"id": 2, "title": "Annapurna Conservation Research Proceedings (2026)", "editor": "National Trust for Nature Conservation", "year": "2026", "status": "published", "pages": 210, "issn": "2392-490X"},
        ],
        "Academic & Field Research Journal Publications (2 items)",
    ),
    (
        "cms_content_trash",
        [],
        "Soft-deleted CMS content items with restore capability",
    ),
]


def seed_global_sections_and_content(apps, schema_editor):
    SiteSetting = apps.get_model("tourist", "SiteSetting")
    for key, value, desc in GLOBAL_SECTIONS:
        SiteSetting.objects.get_or_create(
            key=key,
            defaults={"value": value, "description": desc, "is_public": True},
        )

    for key, value, desc in CONTENT_COLLECTIONS:
        SiteSetting.objects.get_or_create(
            key=key,
            defaults={"value": value, "description": desc, "is_public": True},
        )


def unseed_global_sections_and_content(apps, schema_editor):
    SiteSetting = apps.get_model("tourist", "SiteSetting")
    all_keys = [k for k, _, _ in GLOBAL_SECTIONS] + [k for k, _, _ in CONTENT_COLLECTIONS]
    SiteSetting.objects.filter(key__in=all_keys).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("tourist", "0095_alter_hotel_website"),
    ]

    operations = [
        migrations.RunPython(seed_global_sections_and_content, unseed_global_sections_and_content),
    ]
