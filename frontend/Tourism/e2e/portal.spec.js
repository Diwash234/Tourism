import { test, expect } from "@playwright/test"

test.describe("Public portal surfaces", () => {
  test("landing shows verified destination copy", async ({ page }) => {
    await page.goto("/")
    await expect(page).toHaveTitle(/Nepal Tourism Portal/i)
    await expect(page.getByText("5,800+ Verified Destinations").first()).toBeVisible()
  })

  test("destination search geocodes Pokhara from pkr", async ({ page }) => {
    await page.goto("/destinations")
    const search = page.getByTestId("destination-search")
    await expect(search).toBeVisible()
    await search.fill("pkr")
    await expect(page.getByText("Pokhara & Phewa Lake (पोखरा)")).toBeVisible()
    await expect(page.getByText(/28\.210°/)).toBeVisible()
    await expect(page.getByText(/83\.986°/)).toBeVisible()
  })

  test("gallery heading loads", async ({ page }) => {
    await page.goto("/gallery")
    await expect(page.getByText("Nepal Destination Photography & Visual Stories")).toBeVisible()
  })

  test("compare page lists landmark destinations", async ({ page }) => {
    await page.goto("/compare")
    await expect(page.getByText("Compare Nepal Destinations & Treks")).toBeVisible()
    await expect(page.getByText("Pokhara & Phewa Lake").first()).toBeVisible()
    await expect(page.getByText("Everest Base Camp (EBC)").first()).toBeVisible()
  })

  test("navigation HUD is available", async ({ page }) => {
    await page.goto("/navigation")
    await expect(page.getByTestId("navigation-page")).toBeVisible()
    await expect(page.getByText("Nepal Route Navigation & Tactical HUD")).toBeVisible()
  })
})
