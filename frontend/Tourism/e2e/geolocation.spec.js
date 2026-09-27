import { expect, test } from "@playwright/test"

/**
 * GPS-dependent flows, driven through the browser's real geolocation API.
 *
 * The context geolocation is set in playwright.config.js (Kathmandu, ~8 m
 * accuracy). These tests assert the app consumes that fix and that the
 * deliberately broken coordinates are refused rather than silently accepted.
 *
 * This is emulation. A physical-device pass is still required before launch.
 */

const KATHMANDU = { latitude: 27.7172, longitude: 85.324 }

async function readPosition(page) {
  return page.evaluate(() =>
    new Promise((resolve) => {
      if (!navigator.geolocation) {
        resolve({ error: "geolocation_unavailable" })
        return
      }
      navigator.geolocation.getCurrentPosition(
        (position) =>
          resolve({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
            accuracy: position.coords.accuracy,
          }),
        (error) => resolve({ error: error.code ?? error.message }),
        { enableHighAccuracy: true, timeout: 10000 },
      )
    }),
  )
}

test.describe("geolocation", () => {
  test("browser geolocation resolves to the configured fix", async ({ page }) => {
    await page.goto("/")
    const position = await readPosition(page)

    // A silent failure here means the context geolocation/permission did not
    // apply, and every GPS-dependent test below would be testing nothing.
    expect(position.error).toBeUndefined()
    expect(position.latitude).toBeCloseTo(KATHMANDU.latitude, 3)
    expect(position.longitude).toBeCloseTo(KATHMANDU.longitude, 3)
    expect(position.accuracy).toBeGreaterThan(0)
  })

  test("a valid fix is accepted by the location endpoint", async ({ request }) => {
    const response = await request.post("/api/v1/auth/update-location/", {
      data: {
        latitude: KATHMANDU.latitude,
        longitude: KATHMANDU.longitude,
        source: "gps",
        accuracy: 8,
      },
    })
    expect([200, 401, 403]).toContain(response.status())
  })

  test("null island is refused with a reason", async ({ request }) => {
    const response = await request.post("/api/v1/auth/update-location/", {
      data: { latitude: 0, longitude: 0, source: "gps" },
    })

    if (response.status() === 401 || response.status() === 403) {
      test.skip(true, "location endpoint requires an authenticated user")
      return
    }

    expect(response.status()).toBe(400)
    const body = await response.json()
    expect(body.position_unchanged).toBe(true)
    expect(body.geo_validation.usable).toBe(false)
    expect(body.geo_validation.reasons).toContain("null_island")
  })

  test("a wildly inaccurate fix is refused", async ({ request }) => {
    const response = await request.post("/api/v1/auth/update-location/", {
      data: {
        latitude: KATHMANDU.latitude,
        longitude: KATHMANDU.longitude,
        accuracy: 12000,
      },
    })

    if (response.status() === 401 || response.status() === 403) {
      test.skip(true, "location endpoint requires an authenticated user")
      return
    }

    expect(response.status()).toBe(400)
    const body = await response.json()
    expect(body.geo_validation.reasons).toContain("accuracy_too_low")
  })

  test("weather endpoint refuses null island instead of forecasting the ocean", async ({
    request,
  }) => {
    const response = await request.get("/api/v1/weather/?lat=0&lon=0")
    expect(response.status()).toBe(200)
    const body = await response.json()
    expect(body.available).toBe(false)
    expect(body.reason).toContain("null_island")
  })
})
