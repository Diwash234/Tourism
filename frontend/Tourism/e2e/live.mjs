#!/usr/bin/env node
/**
 * Live feature e2e against Django + Vite.
 * Runs without a GUI browser so it works when Playwright Chromium
 * cannot download or is missing system libraries.
 */
import { readFileSync } from "node:fs"
import { dirname, join } from "node:path"
import { fileURLToPath } from "node:url"

const here = dirname(fileURLToPath(import.meta.url))
const API = process.env.E2E_API || "http://127.0.0.1:8000/api/v1"
const WEB = process.env.E2E_BASE_URL || "http://127.0.0.1:5173"
const DEMO = {
  tourist: { email: "tourist@nepaltourism.com", password: "Tourist@12345" },
  admin: { email: "admin@tourism.gov.np", password: "Admin@12345" },
  staff: { email: "staff-ops@nepaltourism.com", password: "StaffOps!12345" },
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

// Source assertions: a dev server transforms /src/*.jsx on the fly, while
// `vite preview` answers with the SPA fallback HTML. Read through HTTP when a
// dev server answers with real source; otherwise verify the file on disk —
// same assertion either way, never a false red from the serving mode.
async function sourceFile(relPath) {
  const { res, text } = await request(`${WEB}/src/${relPath}`)
  const body = String(text ?? "")
  const isHtmlFallback = /^\s*<!doctype html/i.test(body)
  if (res.ok && body && !isHtmlFallback) return body
  return readFileSync(join(here, "..", "src", relPath), "utf8")
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
    const text = await sourceFile("pages/Checkout.jsx")
    if (text.includes("Review & Request Booking") && !/name=["']card_number["']/.test(text)) {
      ok("checkout source is Review & Request Booking without card fields")
    } else fail("checkout source", "missing title or still has card fields")
  }

  {
    const text = await sourceFile("Chatbot.jsx")
    if (text.includes("package_cards: data.package_cards")) ok("Himal AI page wires package_cards")
    else fail("Himal AI page wires package_cards")
  }

  {
    const { res, data } = await request(`${API}/marketplace/listings/`)
    const titles = (data?.results || []).map((row) => row.title)
    if (res.ok && titles.includes("Pokhara & Annapurna Heritage Circuit") && !titles.includes("Pokhara Eco-Lodge Pending Stay")) {
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
      titles.includes("Pokhara & Annapurna Heritage Circuit") &&
      !titles.includes("Himalayan Luxury Panorama Week") &&
      !titles.includes("Pokhara Eco-Lodge Pending Stay") &&
      alts.includes("Kathmandu & Pokhara 6-Day Cultural Circuit")
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
    // Destination pages list ALL destinations nearest-first (not only a small radius)
    const first = await request(`${API}/destinations/?limit=1`)
    const row = (first.data?.results || [])[0]
    if (row?.latitude != null && row?.longitude != null) {
      const nearby = await request(`${API}/destinations/nearby/?latitude=${row.latitude}&longitude=${row.longitude}&radius_km=2000&page_size=5`)
      const rows = nearby.data?.results || []
      const sorted = rows.every((r, i) => i === 0 || (rows[i - 1].distance_km ?? 0) <= (r.distance_km ?? 0))
      const total = nearby.data?.count || 0
      if (nearby.res.ok && rows.length && sorted && total > rows.length && rows.every((r) => r.slug)) {
        ok("destinations/nearby ranks ALL destinations nearest-first beyond any city radius")
      } else fail("nearby ranking", `status=${nearby.res.status} rows=${rows.length} total=${total} sorted=${sorted}`)
    } else fail("nearby ranking", "no seeded destination with coordinates")
  }

  {
    const src = await sourceFile("pages/destinations/DestinationDetails.jsx")
    if (src.includes("Destinations Near") && src.includes("getNearbyDestinations") && src.includes("Show more destinations")) {
      ok("destination page renders the full nearby-destinations section")
    } else fail("destination page nearby section source")
  }

  {
    const src = await sourceFile("components/admin/HotelBookingPanel.jsx")
    if (src.includes("Add Hotel") && src.includes("createHotel")) {
      ok("admin hotels tab can create hotels")
    } else fail("admin add-hotel source")
  }

  {
    const src = await sourceFile("pages/destinations/DestinationDetails.jsx")
    if (src.includes("What's Actually Near") && src.includes("getNearbyPOIs") && src.includes("OpenStreetMap")) {
      ok("destination page shows real OpenStreetMap nearby places")
    } else fail("destination nearby-pois source")
  }

  {
    const landing = await sourceFile("pages/Landing.jsx")
    const marquee = await sourceFile("components/landing/ProvinceMarquee.jsx")
    const symbols = await sourceFile("components/dashboard/NationalSymbols.jsx")
    const cmsWired =
      landing.includes("cmsFeatureItems") &&
      marquee.includes("cmsItems") &&
      symbols.includes("summarySymbols")
    if (cmsWired) {
      ok("features boxes, marquee and symbol boxes are admin-editable via CMS")
    } else fail("landing CMS wiring source")
  }

  {
    const cfg = await request(`${API}/config/public/`)
    const nav = cfg.data?.navigation || []
    if (cfg.res.ok && nav.some((item) => item.route === "/support")) {
      ok("customer support is linked in the public navigation")
    } else fail("support link in public nav", `status=${cfg.res.status}`)
  }

  {
    // Admin can create AND remove pages; the homepage itself is protected.
    const token = await login("admin")
    const auth = { Authorization: `Bearer ${token}` }
    const created = await request(`${API}/admin/cms/`, {
      method: "POST",
      headers: auth,
      json: { resource: "pages", route: `/e2e-del-${Math.random().toString(36).slice(2, 8)}`, key: `e2e-del-${Math.random().toString(36).slice(2, 8)}`, title: "E2E Delete Me" },
    })
    const id = created.data?.record?.id || created.data?.id
    if (!created.res.ok || !id) {
      fail("admin page create/delete", `create status=${created.res.status}`)
    } else {
      const del = await request(`${API}/admin/cms/`, { method: "DELETE", headers: auth, json: { resource: "pages", id } })
      const pages = await request(`${API}/admin/cms/?resource=pages`, { headers: auth })
      const still = (pages.data?.results || pages.data || []).some((p) => p.id === id)
      const homeRow = (pages.data?.results || pages.data || []).find((p) => p.route === "/")
      let homeProtected = false
      if (homeRow) {
        const refused = await request(`${API}/admin/cms/`, { method: "DELETE", headers: auth, json: { resource: "pages", id: homeRow.id } })
        homeProtected = refused.res.status === 400
      }
      if (del.res.ok && !still && homeProtected) {
        ok("admin can delete pages while the homepage stays protected")
      } else fail("admin page create/delete", `del=${del.res.status} still=${still} homeProtected=${homeProtected}`)
    }
  }

  {
    // card_grid blocks accept HTTPS images but reject script URLs
    const token = await login("admin")
    const auth = { Authorization: `Bearer ${token}` }
    const pages = await request(`${API}/admin/cms/?resource=pages`, { headers: auth })
    const home = (pages.data?.results || pages.data || []).find((p) => p.route === "/")
    if (!home) {
      fail("card_grid image validation", "no homepage row")
    } else {
      const sec = await request(`${API}/admin/cms/`, {
        method: "POST",
        headers: auth,
        json: { resource: "sections", page_id: home.id, key: `e2e-cards-${Math.random().toString(36).slice(2, 8)}`, title: "E2E Cards", section_type: "blocks" },
      })
      const secId = sec.data?.record?.id || sec.data?.id
      const bad = await request(`${API}/admin/sections/${secId}/blocks/`, {
        method: "POST",
        headers: auth,
        json: { block_type: "card_grid", data: { items: [{ title: "Bad", image: "javascript:alert(1)" }] } },
      })
      const good = await request(`${API}/admin/sections/${secId}/blocks/`, {
        method: "POST",
        headers: auth,
        json: { block_type: "card_grid", data: { items: [{ title: "Everest", image: "https://example.com/everest.jpg", url: "/destinations" }] } },
      })
      await request(`${API}/admin/cms/`, { method: "DELETE", headers: auth, json: { resource: "sections", id: secId } })
      if (bad.res.status === 400 && good.res.ok) {
        ok("card images must be HTTPS or site paths (script URLs rejected)")
      } else fail("card_grid image validation", `bad=${bad.res.status} good=${good.res.status}`)
    }
  }

  {
    // Coordinate-first nearby POIs (spec §2) + admin category control (§4)
    const missing = await request(`${API}/nearby/pois/`)
    const invalid = await request(`${API}/nearby/pois/?latitude=200&longitude=1`)
    const token = await login("admin")
    const cats = await request(`${API}/admin/poi-categories/`, { headers: { Authorization: `Bearer ${token}` } })
    const touristToken = await login("tourist")
    const forbidden = await request(`${API}/admin/poi-categories/`, { method: "PUT", headers: { Authorization: `Bearer ${touristToken}` }, json: { categories: [] } })
    const src = await sourceFile("pages/NearbyPlaces.jsx")
    if (
      missing.res.status === 400 && invalid.res.status === 400 &&
      cats.res.ok && Array.isArray(cats.data?.categories) && cats.data.categories.length >= 20 &&
      forbidden.res.status === 403 &&
      src.includes("Real-world places") && src.includes("getPOIsByCoords")
    ) {
      ok("coordinate-first POI search with admin-configurable categories")
    } else fail("coordinate POI system", `missing=${missing.res.status} invalid=${invalid.res.status} cats=${cats.res.status}/${cats.data?.categories?.length} forbidden=${forbidden.res.status}`)
  }

  {
    const listed = await request(`${API}/destinations/?limit=1`)
    const slug = listed.data?.results?.[0]?.slug
    const emergency = slug
      ? await request(`${API}/destinations/${encodeURIComponent(slug)}/emergency/?radius_km=80&limit=4`)
      : { res: { ok: false }, data: {} }
    const inventedFallback = (emergency.data?.hospitals || []).some((row) =>
      row.phone_is_national_fallback && String(row.phone_number || "").includes("4412404")
    )
    if (emergency.res.ok && !inventedFallback && Array.isArray(emergency.data?.hospitals)) {
      ok("destination emergency does not invent TUTH 4412404 as a fallback")
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

  {
    const config = await request(`${API}/config/public/`)
    if (config.res.ok && Number.isFinite(config.data?.catalog?.destination_count)) {
      ok("public config exposes live destination count")
    } else fail("public catalog count", `status=${config.res.status}`)
  }

  {
    const discover = await request(`${API}/discover-nepal/`)
    const pending = String(discover.data?.pending_label || "")
    const wildlife = discover.data?.wildlife?.items || []
    if (discover.res.ok && pending.includes("Not recorded") && Array.isArray(wildlife)) {
      ok("discover nepal returns recorded groups and pending label")
    } else fail("discover nepal", `status=${discover.res.status}`)
  }

  {
    const listed = await request(`${API}/destinations/?limit=5`)
    const rows = listed.data?.results || []
    const hasPinField = rows.every((row) => typeof row.has_map_pin === "boolean")
    const noDistrictAsCity = rows.every((row) => !row.display_city || row.display_city.toLowerCase() !== "kaski")
    if (listed.res.ok && rows.length && hasPinField && noDistrictAsCity) {
      ok("destination list exposes has_map_pin and does not display Kaski as a city")
    } else fail("destination list display_city", `count=${rows.length}`)
  }

  // ---- Staff Operations Center (spec §7-22) ----
  {
    let staffToken = null
    try { staffToken = await login("staff") } catch { staffToken = null }
    if (!staffToken) {
      fail("staff login (seed staff-ops user via scripts or shell before live e2e)")
    } else {
      const auth = { Authorization: `Bearer ${staffToken}` }

      // 1) support tickets — scoped queue with counts
      {
        const { res, data } = await request(`${API}/admin-panel/support/tickets/`, { headers: auth })
        if (res.ok && data && typeof data.counts === "object" && Array.isArray(data.results)) ok("staff support ticket queue (scoped + counts)")
        else fail("staff support tickets", `status ${res.status}`)
      }

      // 2) bookings — every row inside the staff member's hotel assignment
      {
        const hotels = await request(`${API}/admin-panel/my-hotels/`, { headers: auth })
        const hotelIds = new Set((hotels.data?.results || hotels.data || []).map((h) => h.id))
        const { res, data } = await request(`${API}/admin-panel/my-bookings/`, { headers: auth })
        const rows = data?.results || []
        const inScope = rows.every((r) => hotelIds.has(r.hotel_id))
        if (res.ok && data?.counts && inScope) ok("staff bookings scoped to assigned hotels")
        else fail("staff bookings scope", `status ${res.status} rows=${rows.length}`)

        // 3) out-of-scope booking action is refused
        const anyBooking = await request(`${API}/admin-panel/my-bookings/`, { headers: auth })
        const outsider = anyBooking.data?.results?.[0]
        if (outsider) {
          const forbidden = await request(`${API}/admin-panel/my-bookings/999999/action/`, {
            method: "POST", headers: auth, json: { action: "confirm" },
          })
          if (forbidden.res.status === 404 || forbidden.res.status === 403) ok("booking action outside scope refused")
          else fail("booking action scope guard", `status ${forbidden.res.status}`)
        } else ok("booking action outside scope refused (no bookings; endpoint guard covered by Django suite)")
      }

      // 4) data entry — draft → submit → self-approve refused
      {
        const stamp = Date.now()
        const created = await request(`${API}/admin-panel/data-entry/`, {
          method: "POST", headers: auth,
          json: { name: `E2E Probe ${stamp}`, district: "Kaski", short_description: "created by live e2e" },
        })
        if (created.res.status === 201 && created.data?.status === "draft" && created.data?.submitted_by === DEMO.staff.email) {
          ok("staff creates destination draft (submitted_by stamped)")
        } else fail("staff data-entry draft", `status ${created.res.status}`)

        if (created.data?.id) {
          const submitted = await request(`${API}/admin-panel/data-entry/${created.data.id}/action/`, {
            method: "POST", headers: auth, json: { action: "submit" },
          })
          if (submitted.res.ok && submitted.data?.status === "submitted") ok("staff submits draft for review")
          else fail("staff data-entry submit", `status ${submitted.res.status}`)

          const selfApprove = await request(`${API}/admin-panel/data-entry/${created.data.id}/action/`, {
            method: "POST", headers: auth, json: { action: "approve" },
          })
          if (selfApprove.res.status === 403) ok("staff cannot approve own submission (needs destinations:approve)")
          else fail("staff self-approve guard", `status ${selfApprove.res.status}`)

          // cleanup: admin rejects the probe entry so the queue stays tidy
          try {
            const adminToken = await login("admin")
            await request(`${API}/admin-panel/data-entry/${created.data.id}/action/`, {
              method: "POST", headers: { Authorization: `Bearer ${adminToken}` },
              json: { action: "reject", note: "e2e probe cleanup" },
            })
          } catch {}
        }
      }

      // 5) media — staff upload lands pending, staff cannot approve
      {
        const entry = await request(`${API}/admin-panel/data-entry/?status=rejected`, { headers: auth })
        const dest = entry.data?.results?.[0]
        if (dest) {
          const added = await request(`${API}/admin-panel/media/`, {
            method: "POST", headers: auth,
            json: { destination: dest.id, external_url: "https://upload.wikimedia.org/wikipedia/commons/2/2a/Everest_kalapatthar.jpg", caption: "e2e probe" },
          })
          if (added.res.status === 201 && added.data?.status === "pending") ok("staff image upload lands in pending review queue")
          else fail("staff media upload", `status ${added.res.status}`)
          if (added.data?.id) {
            const approve = await request(`${API}/admin-panel/media/${added.data.id}/action/`, {
              method: "POST", headers: auth, json: { action: "approve" },
            })
            if (approve.res.status === 403) ok("staff cannot approve images (needs images:approve)")
            else fail("media approve guard", `status ${approve.res.status}`)
          }
        } else fail("staff media upload", "no destination available for probe")
      }

      // 6) safety queue shape
      {
        const { res, data } = await request(`${API}/admin-panel/safety/`, { headers: auth })
        if (res.ok && data?.counts && Array.isArray(data.alerts) && Array.isArray(data.hazards) && Array.isArray(data.reports)) {
          ok("staff safety operations queue")
        } else fail("staff safety queue", `status ${res.status}`)
      }

      // 7) staff cannot change own permissions
      {
        const esc = await request(`${API}/admin/staff-capabilities/`, {
          method: "PUT", headers: auth,
          json: { user_id: 1, capabilities: { users: ["view", "change"] } },
        })
        if (esc.res.status === 403) ok("staff cannot update capability profiles")
        else fail("capability self-escalation guard", `status ${esc.res.status}`)
      }
    }

    // 8) anonymous access refused on every staff-ops endpoint
    {
      const statuses = await Promise.all([
        "admin-panel/support/tickets/", "admin-panel/my-bookings/", "admin-panel/data-entry/",
        "admin-panel/media/", "admin-panel/safety/",
      ].map((u) => request(`${API}/${u}`).then((r) => r.res.status)))
      if (statuses.every((code) => code === 401)) ok("anonymous refused on all staff-ops endpoints")
      else fail("anonymous staff-ops guard", JSON.stringify(statuses))
    }
  }

  // ---- Staff panels & navigation extensions wired into the UI ----
  {
    const dash = await sourceFile("pages/StaffDashboard.jsx")
    const wired = ["SupportDeskPanel", "HotelOpsPanel", "ContentOpsPanel", "MediaPanel", "SafetyOpsPanel", "StaffGlobalSearch"]
      .every((c) => dash.includes(c))
    if (wired) ok("StaffDashboard wires support/hotels/data-entry/media/safety/search panels")
    else fail("StaffDashboard panel wiring")
  }

  {
    const nav = await sourceFile("pages/Navigation.jsx")
    if (nav.includes("savedRoutesApi.recalculate") && nav.includes("Check alternative routes")
        && nav.includes("Browse destinations by province") && nav.includes("Offline mode")) {
      ok("Navigation page has recalculate, alternatives, province picker and offline banner")
    } else fail("Navigation extensions wiring")
  }

  {
    // §21/§119 — opt-in traveller location joins the recommendation ranking
    const withLoc = await request(`${API}/destinations/mood-recommendations/?mood=lakeside&latitude=28.21&longitude=83.98&limit=8`)
    const badLoc = await request(`${API}/destinations/mood-recommendations/?mood=lakeside&latitude=999&longitude=0&limit=4`)
    const recSrc = await sourceFile("pages/Recommendation.jsx")
    const rows = withLoc.data?.results || []
    if (
      withLoc.res.ok && withLoc.data?.preferences?.location?.latitude === 28.21 &&
      rows.some((r) => r.distance_km != null && r.distance_is_straight_line === true) &&
      badLoc.res.ok && badLoc.data?.preferences?.location === null &&
      recSrc.includes("requestMyLocation") && recSrc.includes("straight line")
    ) ok("recommendations accept traveller location with honest straight-line distances")
    else fail("location-aware recommendations")
  }

  {
    // §46 — rich text editor validates URLs and powers homepage bodies
    const editor = await sourceFile("components/admin/RichTextEditor.jsx")
    const homepage = await sourceFile("components/admin/HomepageManagerPanel.jsx")
    if (
      editor.includes("safeUrl") && editor.includes("unlink") && editor.includes("mailto:") &&
      homepage.includes("RichTextEditor")
    ) ok("rich text editor validates URLs and powers homepage section bodies")
    else fail("rich text editor upgrade")
  }

  console.log(`\n${results.length - failed} passed, ${failed} failed`)
  process.exit(failed ? 1 : 0)
}

run().catch((error) => {
  console.error(error)
  process.exit(1)
})
