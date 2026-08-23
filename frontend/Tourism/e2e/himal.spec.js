import { test, expect } from "@playwright/test"

test.describe("Himal AI published packages", () => {
  test("5-day under $500 returns the live published circuit, not invented or over-budget offers", async ({ page }) => {
    await page.goto("/chatbot")
    await expect(page.getByTestId("himal-page")).toBeVisible()
    await page.getByTestId("himal-quick-budget").click()
    await expect(page.getByTestId("himal-package-cards")).toBeVisible({ timeout: 20_000 })
    await expect(page.getByText("E2E Five Day Nepal Circuit").first()).toBeVisible()
    await expect(page.getByText("E2E Luxury Over Budget Week")).toHaveCount(0)
    await expect(page.getByText("E2E Hidden Pending Stay")).toHaveCount(0)
    await expect(page.getByText("E2E Six Day Alternative Circuit").first()).toBeVisible()
    await expect(page.getByTestId("himal-package-alternative").first()).toBeVisible()
    await page.getByTestId("himal-package-add").first().click()
    await page.goto("/checkout")
    await expect(page.getByText("E2E Five Day Nepal Circuit").first()).toBeVisible()
  })

  test("impossible budget uses the honest no-match copy", async ({ page }) => {
    await page.goto("/chatbot")
    await page.getByTestId("himal-input").fill("I want a 5-day trip to Nepal under $1")
    await page.getByTestId("himal-send").click()
    await expect(page.getByText("I couldn't find a published package matching those requirements right now.")).toBeVisible({ timeout: 20_000 })
  })
})
