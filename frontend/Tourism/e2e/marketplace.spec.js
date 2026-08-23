import { test, expect } from "@playwright/test"

test.describe("Marketplace public surfaces", () => {
  test("packages page explains request-to-book and never asks for a card", async ({ page }) => {
    await page.goto("/packages")
    await expect(page.locator("text=Travel Packages")).toBeVisible()
    await expect(page.locator("text=we never take card numbers here")).toBeVisible()
  })

  test("checkout is titled Review & Request Booking", async ({ page }) => {
    await page.goto("/checkout")
    await expect(page.locator("text=Review & Request Booking")).toBeVisible()
    await expect(page.locator("text=Card numbers are never accepted here")).toBeVisible()
  })
})
