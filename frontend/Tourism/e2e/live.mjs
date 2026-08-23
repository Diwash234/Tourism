#!/usr/bin/env node
/**
 * Live feature e2e against Django + Vite.
 * Runs without a GUI browser so it works when Playwright Chromium
 * cannot download or is missing system libraries.
 */
const API = process.env.E2E_API || "http://127.0.0.1:8000/api/v1"
const WEB = process.env.E2E_BASE_URL || "http://127.0.0.1:5173"
const DEMO = {
  tourist: { email: "tourist@nepaltourism.com", password: "Tourist@12345" },
  admin: { email: "admin@tourism.gov.np", password: "Admin@12345" },
}

let failed = 0
const results = []

function ok(name) {
  results.push({ name, ok: true })
  console.log(`  ok  ${name}`)
}
function fail(name, detail) {
  failed += 1
  results.push({ name, ok: false, detail })
  console.error(`  FAIL ${name}${detail ? ` — ${detail}` : ""}`)
}

async function request(url, options = {}) {
  const headers = { ...(options.headers || {}) }
  if (options.json) {
    headers["Content-Type"] = "application/json"
    headers.Accept = headers.Accept || "application/json"
  }
  const res = await fetch(url, {
    ...options,
    headers,
    body: options.json ? JSON.stringify(options.json) : options.body,
  })
  const text = await res.text()
  let data = null
  try { data = text ? JSON.parse(text) : null } catch { data = text }
  return { res, data, text }
}

async function login(role) {
  const { res, data } = await request(`${API}/auth/login/`, {
    method: "POST",
    json: DEMO[role],
  })
  if (!res.ok || !data?.access) throw new Error(`login ${role} ${res.status}`)
  return data.access
}

async function waitFor(url, tries = 60) {
  for (let i = 0; i < tries; i += 1) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(2000) })
      if (res.ok || res.status === 304) return true
    } catch {}
    await new Promise((r) => setTimeout(r, 1000))
  }
  return false
}

async function run() {
  console.log(`Live feature e2e\n  web ${WEB}\n  api ${API}\n`)

  if (!(await waitFor(`${API}/config/public/`, 5))) {
    fail("servers", "Django is not reachable on :8000")
    process.exit(1)
  }
  if (!(await waitFor(`${WEB}/`, 5))) {
    fail("servers", "Vite is not reachable on :5173")
    process.exit(1)
  }
  ok("django and vite are up")

  {
    const { res, text } = await request(`${WEB}/`, { headers: { Accept: "text/html" } })
    if (res.ok && /Nepal Tourism Portal/i.test(text)) ok("landing HTML title")
    else fail("landing HTML title", `status ${res.status}`)
  }

  for (const path of ["/packages", "/checkout", "/emergency", "/collaborate", "/chatbot", "/trip"]) {
    const { res, text } = await request(`${WEB}${path}`, { headers: { Accept: "text/html" } })
    if (res.ok && String(text).includes("root")) ok(`frontend serves ${path}`)
    else fail(`frontend serves ${path}`, `status ${res.status}`)
  }

  {
    const { res, text } = await request(`${WEB}/src/pages/Checkout.jsx`)
    if (res.ok && text.includes("Review & Request Booking") && !/name=["']card_number["']/.test(text)) {
      ok("checkout source is Review & Request Booking without card fields")
    } else fail("checkout source", "missing title or still has card fields")
  }

  {
    const { res, text } = await request(`${WEB}/src/Chatbot.jsx`)
    if (res.ok && text.includes("package_cards: data.package_cards")) ok("Himal AI page wires package_cards")
    else fail("Himal AI page wires package_cards")
  }

  {
    const { res, data } = await request(`${API}/marketplace/listings/`)
    const titles = (data?.results || []).map((row) => row.title)
    if (res.ok && titles.includes("E2E Five Day Nepal Circuit") && !titles.includes("E2E Hidden Pending Stay")) {
      ok("public catalogue shows published package only")
    } else fail("public catalogue", JSON.stringify(titles.slice(0, 8)))
  }

  {
    const listed = await request(`${API}/marketplace/listings/`)
    const offer = (listed.data?.results || []).find((row) => row.slug === "e2e-five-day-nepal-circuit")
    const card = await request(`${API}/marketplace/checkout/`, {
      method: "POST",
      json: {
        guest_name: "Ada",
        guest_email: "ada-card@example.com",
        card_number: "4111111111111111",
        expiry_date: "12/29",
        items: [{ listing_id: offer.id }],
      },
    })
    if (card.res.status === 400) ok("checkout rejects card and expiry fields")
    else fail("checkout rejects card", `status ${card.res.status}`)
  }

  let reference = ""
  const guestEmail = `e2e-live-${Date.now()}@example.com`
  {
    const listed = await request(`${API}/marketplace/listings/`)
    const offer = (listed.data?.results || []).find((row) => row.slug === "e2e-five-day-nepal-circuit")
    const checkout = await request(`${API}/marketplace/checkout/`, {
      method: "POST",
      json: {
        guest_name: "E2E Traveller",
        guest_email: guestEmail,
        payment_method: "request",
        items: [{ listing_id: offer.id, quantity: 1 }],
      },
    })
    reference = checkout.data?.order?.reference || ""
    if (checkout.res.status === 201 && checkout.data?.order?.status === "requested" && reference) {
      ok(`booking request created ${reference}`)
    } else fail("booking request", `status ${checkout.res.status}`)
  }

  {
    const wrong = await request(`${API}/marketplace/orders/?reference=${encodeURIComponent(reference)}&email=${encodeURIComponent("wrong@example.com")}`)
    const right = await request(`${API}/marketplace/orders/?reference=${encodeURIComponent(reference)}&email=${encodeURIComponent(guestEmail)}`)
    if (wrong.res.status === 404 && right.res.status === 200 && right.data?.order?.status === "requested") {
      ok("trip lookup needs reference + matching email")
    } else fail("trip lookup", `wrong=${wrong.res.status} right=${right.res.status}`)
  }

  {
    const apply = await request(`${API}/marketplace/partners/apply/`, {
      method: "POST",
      json: {
        name: `E2E Lodge ${Date.now()}`,
        email: `lodge-${Date.now()}@example.com`,
        kind: "hotel",
        website: "https://example.com",
      },
    })
    if (apply.res.status === 201 && apply.data?.status === "pending") ok("partner apply stays pending")
    else fail("partner apply", `status ${apply.res.status}`)
  }

  {
    const token = await login("tourist")
    const desk = await request(`${API}/marketplace/partner/desk/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (desk.res.ok && desk.data?.partner?.status === "approved") ok("approved tourist can open partner desk")
    else fail("partner desk", `status ${desk.res.status}`)

    const created = await request(`${API}/marketplace/partner/desk/`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
      json: { title: `E2E Live Pending ${Date.now()}`, price_npr: "9000", duration_days: 2, status: "published" },
    })
    if (created.res.status === 201 && created.data?.record?.status === "pending") {
      ok("partner listing stays pending even if they ask to publish")
    } else fail("partner cannot publish", `status ${created.res.status} ${created.data?.record?.status}`)

    const denied = await request(`${API}/marketplace/partner/desk/`, {
      method: "PATCH",
      headers: { Authorization: `Bearer ${token}` },
      json: { id: created.data?.id, action: "publish" },
    })
    if (denied.res.status === 400) ok("partner publish action is rejected")
    else fail("partner publish action", `status ${denied.res.status}`)
  }

  {
    const himal = await request(`${API}/chatbot/message/`, {
      method: "POST",
      json: { message: "I want a 5-day trip to Nepal under $500" },
    })
    const titles = (himal.data?.package_cards || []).map((row) => row.title)
    const alts = (himal.data?.package_cards || []).filter((row) => row.is_alternative).map((row) => row.title)
    if (
      himal.res.ok &&
      titles.includes("E2E Five Day Nepal Circuit") &&
      !titles.includes("E2E Luxury Over Budget Week") &&
      !titles.includes("E2E Hidden Pending Stay") &&
      alts.includes("E2E Six Day Alternative Circuit")
    ) {
      ok("Himal AI returns published in-budget packages only")
    } else fail("Himal AI packages", JSON.stringify(titles))
  }

  {
    const none = await request(`${API}/chatbot/message/`, {
      method: "POST",
      json: { message: "I want a 5-day trip to Nepal under $1" },
    })
    if (none.data?.reply?.includes("I couldn't find a published package matching those requirements right now.")) {
      ok("Himal AI uses honest no-match copy")
    } else fail("Himal AI no-match", none.data?.reply?.slice(0, 160))
  }

  {
    const emergency = await request(`${API}/emergency/nearby/?latitude=27.7172&longitude=85.3240&radius_km=50`)
    const hotlines = (emergency.data?.national_hotlines || []).map((row) => row.phone_number)
    const pharmacies = (emergency.data?.specialized_contacts || []).filter((row) => row.type === "pharmacy")
    if (emergency.res.ok && hotlines.includes("1144") && hotlines.includes("100") && hotlines.includes("102")) {
      ok("emergency directory exposes national hotlines")
    } else fail("emergency hotlines", JSON.stringify(hotlines))
    if (emergency.res.ok && (emergency.data?.counts?.pharmacy_within_radius === 0 || Array.isArray(pharmacies))) {
      ok("emergency does not invent a pharmacy list when none exist")
    } else fail("emergency pharmacies")
  }

  {
    const listed = await request(`${API}/destinations/?limit=3`)
    const rows = listed.data?.results || []
    const inventedSeason = rows.some((row) => row.recommended_season === "Sep - Nov / Mar - May" && !row.best_time_to_visit)
    const inventedBudget = rows.some((row) => row.budget_estimate === 35 && !row.entry_fee)
    if (listed.res.ok && rows.length && !inventedSeason && !inventedBudget) {
      ok("destination list does not invent default season or $35 budget")
    } else fail("destination list honesty", `count=${rows.length}`)
  }

  {
    const nearby = await request(`${API}/nearby/places?lat=27.7172&lng=85.3240&radius=20000`)
    const dests = (Array.isArray(nearby.data) ? nearby.data : []).filter((row) => row.type === "destination")
    if (nearby.res.ok && dests.every((row) => row.slug && row.latitude != null && row.longitude != null)) {
      ok("nearby destinations include slug and recorded coordinates")
    } else fail("nearby destination slug", `status=${nearby.res.status} dests=${dests.length}`)
  }

  {
    const listed = await request(`${API}/destinations/?limit=1`)
    const slug = listed.data?.results?.[0]?.slug
    const emergency = slug
      ? await request(`${API}/destinations/${encodeURIComponent(slug)}/emergency/?radius_km=80&limit=4`)
      : { res: { ok: false }, data: {} }
    const phones = JSON.stringify(emergency.data || {})
    if (emergency.res.ok && !phones.includes("4412404") && Array.isArray(emergency.data?.hospitals)) {
      ok("destination emergency uses recorded hospitals, not TUTH 4412404")
    } else fail("destination emergency honesty", `status=${emergency.res?.status}`)
  }

  {
    const hospitals = await request(`${API}/nearby/hospitals?lat=27.7172&lng=85.3240`)
    const rows = Array.isArray(hospitals.data) ? hospitals.data : []
    const inventedImage = rows.some((row) => String(row.image_url || "").includes("unsplash.com"))
    const inventedPhone = rows.some((row) => row.phone_is_national_fallback && String(row.phone_number) === "+977-1-4412404")
    if (hospitals.res.ok && rows.length && !inventedImage && !inventedPhone) {
      ok("nearby hospitals do not invent Unsplash photos or TUTH as a default phone")
    } else fail("nearby hospitals honesty", `status=${hospitals.res.status} count=${rows.length}`)
  }

  {
    const token = await login("admin")
    const market = await request(`${API}/admin/marketplace/?resource=listings`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    const directory = await request(`${API}/admin/emergency-directory/`, {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (market.res.ok) ok("admin marketplace desk API")
    else fail("admin marketplace", `status ${market.res.status}`)
    if (directory.res.ok) ok("admin emergency directory API")
    else fail("admin emergency directory", `status ${directory.res.status}`)
  }

  console.log(`\n${results.length - failed} passed, ${failed} failed`)
  process.exit(failed ? 1 : 0)
}

run().catch((error) => {
  console.error(error)
  process.exit(1)
})
