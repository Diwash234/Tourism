export const DEMO = {
  tourist: { email: "tourist@nepaltourism.com", password: "Tourist@12345", path: "/login" },
  staff: { email: "staff@tourism.gov.np", password: "Staff@12345", path: "/staff/login" },
  admin: { email: "admin@tourism.gov.np", password: "Admin@12345", path: "/admin/login" },
}

export async function loginAs(page, role = "tourist") {
  const creds = DEMO[role]
  await page.goto(creds.path)
  await page.getByTestId("login-email").fill(creds.email)
  await page.getByTestId("login-password").fill(creds.password)
  await page.getByTestId("login-submit").click()
  await page.waitForURL((url) => !url.pathname.includes("/login"), { timeout: 20_000 })
}

export function noCardFields(page) {
  return Promise.all([
    page.locator("input[name='card_number'], input[name='cardNumber'], input[autocomplete='cc-number']").count(),
    page.locator("input[name='cvv'], input[name='cvc'], input[name='pan']").count(),
    page.locator("input[name='expiry'], input[name='expiry_date'], input[name='expiration'], input[name='exp_month'], input[name='exp_year']").count(),
    page.getByPlaceholder(/card number|cvv|cvc|expiry|expiration/i).count(),
  ]).then((counts) => counts.every((n) => n === 0))
}
