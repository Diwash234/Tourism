import { test, expect } from "@playwright/test"
import { loginAs, noCardFields } from "./helpers.js"

test.describe("Marketplace, booking, and partner desk", () => {
  test("packages page lists published offers and never asks for a card", async ({ page }) => {
    await page.goto("/packages")
    await expect(page.getByTestId("packages-page")).toBeVisible()
    await expect(page.getByText("Travel Packages")).toBeVisible()
    await expect(page.getByText("we never take card numbers here")).toBeVisible()
    await expect(page.getByText("Pokhara & Annapurna Heritage Circuit").first()).toBeVisible()
    await expect(page.getByText("Pokhara Eco-Lodge Pending Stay")).toHaveCount(0)
    expect(await noCardFields(page)).toBeTruthy()
  })

  test("checkout is Review & Request Booking and rejects card fields", async ({ page }) => {
    await page.goto("/checkout")
    await expect(page.getByTestId("checkout-page")).toBeVisible()
    await expect(page.getByText("Review & Request Booking")).toBeVisible()
    await expect(page.getByText("Card numbers are never accepted here")).toBeVisible()
    await expect(page.getByTestId("checkout-form")).toBeVisible()
    expect(await noCardFields(page)).toBeTruthy()
  })

  test("add to trip, request booking, then look up with reference + email", async ({ page }) => {
    await page.goto("/packages")
    await expect(page.getByText("Pokhara & Annapurna Heritage Circuit").first()).toBeVisible()
    await page.locator('[data-package-slug="e2e-five-day-nepal-circuit"]').getByTestId("add-to-trip").first().click()
    await page.goto("/checkout")
    const email = `e2e-${Date.now()}@example.com`
    await page.getByTestId("checkout-name").fill("E2E Traveller")
    await page.getByTestId("checkout-email").fill(email)
    await page.getByTestId("checkout-submit").click()
    await expect(page.getByTestId("checkout-result")).toBeVisible()
    const referenceText = await page.getByTestId("checkout-reference").innerText()
    const reference = referenceText.replace("Your trip request", "").trim()
    expect(reference).toMatch(/^NP/i)
    await expect(page.getByText(/Requested/i).first()).toBeVisible()

    await page.goto("/trip")
    await page.getByTestId("trip-reference").fill(reference)
    await page.getByTestId("trip-email").fill("wrong@example.com")
    await page.getByTestId("trip-lookup").click()
    await expect(page.getByText(/No booking request matches|No matching request|not found/i).first()).toBeVisible()

    await page.getByTestId("trip-email").fill(email)
    await page.getByTestId("trip-lookup").click()
    await expect(page.getByTestId("trip-result")).toBeVisible()
    await expect(page.getByText(reference).first()).toBeVisible()
    await expect(page.getByText("Pokhara & Annapurna Heritage Circuit").first()).toBeVisible()
  })

  test("collaborate application submits for review", async ({ page }) => {
    await page.goto("/collaborate")
    await expect(page.getByTestId("collaborate-page")).toBeVisible()
    await page.getByTestId("partner-name").fill(`E2E Lodge ${Date.now()}`)
    await page.getByTestId("partner-email").fill(`lodge-${Date.now()}@example.com`)
    await page.getByTestId("partner-submit").click()
    await expect(page.getByTestId("collaborate-success")).toBeVisible()
    await expect(page.getByText("Application submitted successfully")).toBeVisible()
  })

  test("approved partner desk submits packages as pending and cannot publish", async ({ page }) => {
    await loginAs(page, "tourist")
    await page.goto("/partner")
    await expect(page.getByTestId("partner-desk")).toBeVisible()
    await expect(page.getByText("You cannot publish yourself")).toBeVisible()
    const title = `E2E Partner Pending ${Date.now()}`
    await page.getByTestId("partner-listing-title").fill(title)
    await page.getByTestId("partner-listing-price").fill("12000")
    await page.getByTestId("partner-listing-submit").click()
    await expect(page.getByText(title)).toBeVisible()
    await expect(page.getByText("Waiting for an administrator to publish.")).toBeVisible()
    await page.goto("/packages")
    await expect(page.getByText(title)).toHaveCount(0)
  })

  test("admin marketplace desk is reachable and confirm stays after review", async ({ page }) => {
    await loginAs(page, "admin")
    await page.goto("/admin?section=marketplace")
    await expect(page.getByTestId("marketplace-panel")).toBeVisible()
    await expect(page.getByText("Packages, partners & trip requests")).toBeVisible()
    await page.getByTestId("marketplace-tab-orders").click()
    await expect(page.getByText("Trip requests")).toBeVisible()
    await expect(page.getByText("card numbers are never stored here", { exact: false })).toBeVisible()
  })
})
