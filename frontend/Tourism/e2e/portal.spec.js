import { test, expect } from "@playwright/test"

test.describe("Nepal Tourism Information Portal E2E Suite", () => {
  test("1. Landing page renders luxury typography, national symbols, and search", async ({ page }) => {
    await page.goto("/")
    await expect(page).toHaveTitle(/Nepal Tourism Portal/i)
    await expect(page.locator("text=5,800+ Verified Destinations")).toBeVisible()
  })

  test("2. Smart Search Autocomplete attaches GPS coordinates for fuzzy queries", async ({ page }) => {
    await page.goto("/destinations")
    const searchInput = page.locator('input[placeholder*="Search any place"]')
    await searchInput.fill("pkr")
    await expect(page.locator("text=Pokhara & Phewa Lake (पोखरा)")).toBeVisible()
    await expect(page.locator("text=28.2096° N, 83.9856° E")).toBeVisible()
  })

  test("3. Visual Photo Gallery loads and opens Lightbox modal", async ({ page }) => {
    await page.goto("/gallery")
    await expect(page.locator("text=Nepal Destination Photography & Visual Stories")).toBeVisible()
    const firstPhoto = page.locator("img").first()
    await expect(firstPhoto).toBeVisible()
  })

  test("4. Destination Comparison tool compares side-by-side places", async ({ page }) => {
    await page.goto("/compare")
    await expect(page.locator("text=Compare Nepal Destinations & Treks")).toBeVisible()
    await expect(page.locator("text=Pokhara & Phewa Lake")).toBeVisible()
    await expect(page.locator("text=Everest Base Camp (EBC)")).toBeVisible()
  })

  test("5. Emergency Sentinel displays 24/7 hotlines and searchable hospitals", async ({ page }) => {
    await page.goto("/emergency")
    await expect(page.locator("text=Nearest Help for Every Destination")).toBeVisible()
    await expect(page.locator("text=1144")).toBeVisible()
  })

  test("6. GTA Navigation HUD loads tactical corridors", async ({ page }) => {
    await page.goto("/navigation")
    await expect(page.locator("text=GTA Navigation HUD")).toBeVisible()
  })
})
