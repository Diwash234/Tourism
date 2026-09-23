import { test, expect, chromium } from "@playwright/test"
import { loginAs } from "./helpers.js"

// Environment probe: some sandboxes lack the system libraries Chromium
// needs (libnss3/libnspr4). Skip honestly instead of failing; on any host
// with `npx playwright install --with-deps` these tests run for real.
let browserLaunchable = false
try {
  const probe = await chromium.launch()
  await probe.close()
  browserLaunchable = true
} catch {
  browserLaunchable = false
}
test.skip(!browserLaunchable, "Chromium cannot launch in this environment (missing system libs)")

// Browser-level verification of the Content Lifecycle CMS: a real admin logs
// in and works the panels that manage the real database (6k+ destinations).
test.describe("Admin Content Lifecycle CMS (browser)", () => {
  test.beforeEach(async ({ page }) => {
    await loginAs(page, "admin")
  })

  test("all-content table finds a real record by name", async ({ page }) => {
    await page.goto("/admin?section=content_lifecycle")
    await expect(page.getByText("All Content — Destinations")).toBeVisible()
    // real DB rows render
    await expect(page.locator("table tbody tr").first()).toBeVisible()
    const search = page.getByPlaceholder(/Search id, name, slug/)
    await search.fill("International Mountain Museum")
    await search.press("Enter")
    await expect(page.getByText("International Mountain Museum (Pokhara)")).toBeVisible()
    // provenance flips to manual after the admin correction (acceptance flow)
    await expect(page.getByText("manual").first()).toBeVisible()
  })

  test("all-content search by database id works", async ({ page }) => {
    await page.goto("/admin?section=content_lifecycle")
    const search = page.getByPlaceholder(/Search id, name, slug/)
    await search.fill("5636")
    await search.press("Enter")
    await expect(page.getByText(/International Mountain Museum/).first()).toBeVisible()
  })

  test("data quality shows live counts over the whole dataset", async ({ page }) => {
    await page.goto("/admin?section=content_lifecycle")
    await page.getByRole("button", { name: /Data Quality/ }).click()
    // >6,000 published records in the seeded snapshot
    await expect(page.getByText("Published").locator("..")).toContainText(/6,2\d\d|6,3\d\d/)
    // clicking a quality card jumps into the filtered content view
    await page.getByText("Missing images").click()
    await expect(page.getByText("All Content — Destinations")).toBeVisible()
  })

  test("duplicate review shows live tier counts and evidence", async ({ page }) => {
    await page.goto("/admin?section=content_lifecycle")
    await page.getByRole("button", { name: /Duplicate Review/ }).click()
    await expect(page.getByRole("button", { name: /^high \(\d+\)/ })).toBeVisible()
    // at least one real candidate pair renders with distance evidence
    await expect(page.getByText(/km apart/).first()).toBeVisible()
    await expect(page.getByRole("button", { name: /Not a duplicate/ }).first()).toBeVisible()
  })

  test("import conflicts panel reports an empty queue honestly", async ({ page }) => {
    await page.goto("/admin?section=content_lifecycle")
    await page.getByRole("button", { name: /Import Conflicts/ }).click()
    await expect(page.getByText("No pending conflicts.")).toBeVisible()
  })

  test("approval center renders for the admin", async ({ page }) => {
    await page.goto("/admin?section=content_lifecycle")
    await page.getByRole("button", { name: /Approval Center/ }).click()
    // queue is currently drained (acceptance proposal was approved)
    await expect(
      page.getByText(/Nothing is waiting for approval|Approve & Publish/).first()
    ).toBeVisible()
  })
})
