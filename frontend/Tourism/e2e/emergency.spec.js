import { test, expect } from "@playwright/test"
import { loginAs } from "./helpers.js"

test.describe("Emergency directory", () => {
  test("public page shows national hotlines and coverage next steps", async ({ page }) => {
    await page.goto("/emergency")
    await expect(page.getByTestId("emergency-page")).toBeVisible()
    await expect(page.getByText("Nearest Help for Every Destination")).toBeVisible()
    await expect(page.getByText("1144").first()).toBeVisible()
    await expect(page.getByText("100").first()).toBeVisible()
    await expect(page.getByText("102").first()).toBeVisible()
  })

  test("pharmacy tab does not invent pharmacies", async ({ page }) => {
    await page.goto("/emergency")
    await expect(page.getByTestId("emergency-tab-pharmacy")).toBeVisible({ timeout: 20_000 })
    await page.getByTestId("emergency-tab-pharmacy").click()
    const invented = page.getByText(/invent pharmacies/i)
    const cards = page.locator("article").filter({ hasText: "Pharmacy" })
    const cardCount = await cards.count()
    if (cardCount === 0) {
      await expect(invented).toBeVisible()
      await expect(page.getByRole("link", { name: /Submit a facility/i }).first()).toBeVisible()
    } else {
      await expect(page.getByText(/does not invent pharmacies/i)).toHaveCount(0)
    }
  })

  test("logged-in traveller can open the submit-for-review form", async ({ page }) => {
    await loginAs(page, "tourist")
    await page.goto("/submit-service")
    await expect(page.getByTestId("submit-service-page")).toBeVisible()
    await expect(page.getByText("Help Map Local Nepal")).toBeVisible()
    await expect(page.getByText("Admin approval is required")).toBeVisible()
  })

  test("admin emergency directory desk is available", async ({ page }) => {
    await loginAs(page, "admin")
    await page.goto("/admin?section=emergency_directory")
    await expect(page.getByTestId("emergency-directory-panel")).toBeVisible()
    await expect(page.getByText("does not invent 50–60 pharmacies per ward")).toBeVisible()
  })
})
