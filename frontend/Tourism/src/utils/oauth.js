// Builds the provider's OAuth "authorize" URL client-side, per the exact
// flow documented in the backend's views_oauth.py docstring:
//   1. Redirect the browser here directly (this file)
//   2. Provider redirects back to our own /auth/callback/<provider> with ?code=
//   3. OAuthCallback.jsx POSTs that code to the backend callback endpoint
//
// REQUIRES two env vars this project doesn't have yet — add to your
// .env (not committed): VITE_GOOGLE_CLIENT_ID and VITE_GITHUB_CLIENT_ID.
// These are the OAuth App "Client ID" values (public, safe to expose in
// frontend code) — NOT the client secret, which stays backend-only and
// is already used there (settings.GOOGLE_CLIENT_SECRET /
// GITHUB_CLIENT_SECRET). Get them from:
//   Google: https://console.cloud.google.com/apis/credentials
//   GitHub: https://github.com/settings/developers
// Register the exact redirect URIs below as authorized redirect URIs on
// each provider's app settings, or the provider will reject the request.

// Public client ids served by the backend (/api/v1/config/public/ →
// oauth_client_ids). Lets one backend .env update light up the buttons even
// when VITE_GOOGLE_CLIENT_ID / VITE_GITHUB_CLIENT_ID are not set.
let publicClientIds = { google: "", github: "" }
export function setPublicOAuthIds(ids) {
  publicClientIds = { google: ids?.google || "", github: ids?.github || "" }
}
const googleClientId = () => import.meta.env.VITE_GOOGLE_CLIENT_ID || publicClientIds.google
const githubClientId = () => import.meta.env.VITE_GITHUB_CLIENT_ID || publicClientIds.github
// A real OAuth client id is a long random-ish string (Google: ~28-30 chars
// ending in ".apps.googleusercontent.com", GitHub: 22 chars). Placeholder
// values left in a .env (e.g. "dummy-…-client-id") would make the buttons
// look active and then fail at the provider's consent screen, so treat
// anything that looks like a placeholder as NOT configured.
const looksConfigured = (id) =>
  Boolean(id) && id.length >= 20 && !/dummy|placeholder|your[-_]|example|changeme/i.test(id)
export const hasGoogleClientId = () => looksConfigured(googleClientId())
export const hasGithubClientId = () => looksConfigured(githubClientId())

export function getRedirectUri(provider) {
  return `${window.location.origin}/auth/callback/${provider}`
}

export function getGoogleAuthUrl() {
  const clientId = googleClientId()
  const params = new URLSearchParams({
    client_id: clientId || "",
    redirect_uri: getRedirectUri("google"),
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "select_account",
  })
  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`
}

export function getGithubAuthUrl() {
  const clientId = githubClientId()
  const params = new URLSearchParams({
    client_id: clientId || "",
    redirect_uri: getRedirectUri("github"),
    scope: "read:user user:email",
  })
  return `https://github.com/login/oauth/authorize?${params.toString()}`
}