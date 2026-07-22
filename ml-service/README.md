# Tourism ml-service

A standalone FastAPI microservice that owns everything model/compute-heavy
for the Tourism app: risk scoring, budget estimation, route/itinerary
planning, image classification, translation, recommendations, and a
rule-based chatbot. It does NOT own users, auth, or destinations CRUD -
that stays in your Django `api` app.

## Run it

```bash
cd ml-service
pip install -r requirements.txt
uvicorn app:app --reload --port 8001
```

Or with Docker:

```bash
docker build -t tourism-ml-service .
docker run -p 8001:8001 --env-file .env tourism-ml-service
```

Interactive docs land at `http://localhost:8001/docs` once it's running.

## Train the models (optional to start)

Every model has a rule-based / dictionary fallback, so the API works even
before you've trained anything. When you're ready:

```bash
python training/train_risk_model.py
python training/train_budget_model.py
```

`train_image_classifier.py`, `train_translation_model.py`, and
`build_route_graph.py` are the next ones to fill in once you have real
images in `data/images/raw/`, a real `nepal.osm.pbf`, and a parallel
Nepali/English corpus - the engines in `model/` are already written to
pick the trained artifact up automatically the moment it exists.

## How the three services connect

```
React (Tourism/frontend)  --->  Django (Toursim/Tourism, port 8000)  --->  FastAPI (ml-service, port 8001)
        axios/*Api.js              views_ml.py (proxy views)                api/*.py routers
```

**The frontend never talks to ml-service directly.** It only calls Django
(via `src/api/*.js`, e.g. `recommendationApi.js`, `budgetApi.js`). Django
is the single source of truth for auth (JWT/session cookies) and is what
enforces `ProtectedRoute.jsx` / `AdminRoute.jsx` on the frontend side.

**Django forwards ML requests to this service.** That's what
`views_ml.py` in your `api/` app is for - it receives the authenticated
request from React, does a plain `requests.post()`/`requests.get()` to
this service's internal URL, and returns the JSON straight back to
React. Example view:

```python
# Toursim/Tourism/api/views_ml.py
import requests
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

ML_SERVICE_URL = settings.ML_SERVICE_URL  # e.g. "http://localhost:8001"

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def budget_estimate(request):
    resp = requests.post(
        f"{ML_SERVICE_URL}/budget/estimate",
        json=request.data,
        headers={"X-API-Key": settings.ML_SERVICE_API_KEY},
        timeout=10,
    )
    return Response(resp.json(), status=resp.status_code)
```

Wire it up in `Toursim/Tourism/api/urls.py`:

```python
path("ml/budget/estimate/", views_ml.budget_estimate),
path("ml/risk/predict/", views_ml.risk_predict),
path("ml/recommendation/", views_ml.recommendations),
path("ml/emergency/nearest/", views_ml.emergency_nearest),
# ...one Django view per ml-service route you want to expose
```

And on the frontend, `src/api/budgetApi.js` just calls Django like every
other endpoint already does:

```js
// src/api/budgetApi.js
import axiosClient from "./axiosClient";

export const estimateBudget = (payload) =>
  axiosClient.post("/api/ml/budget/estimate/", payload);
```

**Why route through Django instead of calling FastAPI directly from
React:**
- One CORS origin and one auth system for the frontend to deal with.
- Django can attach the logged-in user, log the request in `models.py`,
  rate-limit, or cache before/after calling ml-service.
- ml-service's port never needs to be exposed publicly - only Django
  needs network access to it (`DJANGO_BACKEND_URL`/`ML_SERVICE_URL` on
  a private network or `localhost` in dev).

**Auth between Django and ml-service:** since end users never hit
ml-service directly, a shared-secret header (`ML_SERVICE_API_KEY` in
`.env`) checked in a small FastAPI dependency is enough - no need for
full OAuth between your own two backend services. Add this to `app.py`
if you want it enforced:

```python
from fastapi import Header, HTTPException

def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != os.getenv("ML_SERVICE_API_KEY"):
        raise HTTPException(status_code=401, detail="Invalid API key")
```

then add `dependencies=[Depends(verify_api_key)]` to `app.include_router(...)`
calls once you're ready to lock it down.

## Endpoint map

| Feature | ml-service route | Suggest Django proxy path |
|---|---|---|
| Risk score | `POST /risk/predict` | `/api/ml/risk/predict/` |
| Budget estimate | `POST /budget/estimate` | `/api/ml/budget/estimate/` |
| Shortest path | `GET /routes/shortest-path` | `/api/ml/routes/shortest-path/` |
| Nearby places | `GET /routes/nearby` | `/api/ml/routes/nearby/` |
| Build itinerary | `POST /routes/itinerary` | `/api/ml/routes/itinerary/` |
| Classify photo | `POST /images/classify` | `/api/ml/images/classify/` |
| Translate phrase | `POST /translation/translate` | `/api/ml/translation/translate/` |
| Recommendations | `GET /recommendation` | `/api/ml/recommendation/` |
| Chatbot | `POST /recommendation/chat` | `/api/ml/chat/` |
| Emergency hotlines | `GET /emergency/hotlines` | `/api/ml/emergency/hotlines/` |
| One category (hospital, pharmacy, bank, police_station, embassy, local_government, hotel) | `GET /emergency/{category}` | `/api/ml/emergency/{category}/` |
| Everything for one city | `GET /emergency/region/{city}` | `/api/ml/emergency/region/{city}/` |
| Nearest emergency facility | `GET /emergency/nearest` | `/api/ml/emergency/nearest/` |
| Valid category list | `GET /emergency/categories` | `/api/ml/emergency/categories/` |
| Languages spoken | `GET /emergency/languages` | `/api/ml/emergency/languages/` |

This maps directly onto your `Emergency.jsx` page: hotlines for the
top-level buttons, `nearest` (fed by `useGeolocation.js`) for "closest
hospital/police/pharmacy/bank to me right now", and `languages` for any
phrasebook widget you add later.

## Folder structure (final)

```
ml-service/
├── app.py
├── requirements.txt
├── Dockerfile
├── .env.example
├── README.md
├── logs/
│   └── .gitkeep                     # ml-service.log is written here at runtime
├── data/
│   ├── destinations/
│   │   └── nepal_destinations_sample.csv
│   ├── languages/
│   │   └── ne-en.tsv                # starter phrase dictionary (not a training corpus)
│   └── emergency/                   # one category per file - nothing mixed together
│       ├── hotlines.json            # police, ambulance, fire, disaster, women/children, traffic
│       ├── hospitals.json
│       ├── pharmacies.json
│       ├── banks.json
│       ├── police_stations.json
│       ├── embassies.json
│       ├── local_government.json
│       ├── hotels.json
│       └── languages.json
├── processed_data/                  # generated by the training scripts
│   ├── risk_features.csv
│   └── budget_features.csv
├── training/
│   ├── train_risk_model.py          # -> model/risk/risk_model.joblib
│   ├── train_budget_model.py        # -> model/budget/budget_model.joblib
│   ├── build_route_graph.py         # -> model/route/nepal_graph.graphml
│   ├── train_image_classifier.py    # -> model/image/classifier.pt (needs real photos, not run yet)
│   └── train_translation_model.py   # -> model/translation/model/ (needs a real corpus, not run yet)
├── model/
│   ├── risk/
│   │   ├── risk_engine.py
│   │   └── risk_model.joblib        # trained, real
│   ├── budget/
│   │   ├── budget_engine.py
│   │   └── budget_model.joblib      # trained, real
│   ├── route/
│   │   ├── route_engine.py
│   │   └── nepal_graph.graphml      # generated, real (straight-line distances - see note below)
│   ├── image/
│   │   └── image_engine.py          # classifier.pt not present yet - see note below
│   └── translation/
│       └── translation_engine.py    # model/translation/model/ not present yet - see note below
├── services/
│   ├── recommendation_service.py
│   ├── itinerary_service.py
│   ├── emergency_service.py
│   └── chatbot_service.py
└── api/
    ├── risk.py
    ├── budget.py
    ├── routes.py
    ├── images.py
    ├── translation.py
    ├── recommendation.py
    └── emergency.py
```

## Notes on what's real vs. placeholder right now

- **Risk & budget models**: `risk_model.joblib` and `budget_model.joblib`
  are already trained and included - `source: "model"` in the API
  response confirms it's using them, not the fallback. Re-run
  `training/train_risk_model.py` / `train_budget_model.py` once you have
  real `data/risk/incidents.csv` and `data/budget/trip_expenses.csv` data
  to replace the synthesized starter data they currently train on.
- **Route graph**: `nepal_graph.graphml` is generated and included, built
  by `training/build_route_graph.py` from the sample destinations, with
  straight-line (haversine) distance as edge weight - not real road
  routing yet. `route_engine.py` loads this file automatically; swapping
  in real OSM-based routing later (via `osmnx` + `nepal.osm.pbf`) is a
  one-function change documented at the top of `build_route_graph.py`.
- **Image classification**: `classifier.pt` is deliberately NOT included.
  Training on empty/no image folders would only produce random,
  meaningless weights - worse than being upfront that it doesn't exist
  yet. `training/train_image_classifier.py` is ready to run the moment
  you add real labeled photos under `data/images/raw/<category>/`.
  Until then, `image_engine.py` returns a clear "not trained yet"
  response instead of failing.
- **Translation model**: same story - `model/translation/model/` is NOT
  included because `data/languages/ne-en.tsv` right now is a ~10-phrase
  starter dictionary, not a real parallel corpus. `translation_engine.py`
  uses that dictionary directly for now; `training/train_translation_model.py`
  is ready to fine-tune a real model once you have thousands of aligned
  sentence pairs.
- **Emergency directory**: fully real, static data, one category per
  file as shown above - extend the relevant file (e.g. add a hospital to
  `hospitals.json`) and it's live with no code changes.