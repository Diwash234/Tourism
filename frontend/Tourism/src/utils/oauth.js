// Builds the provider's OAuth "authorize" URL client-side, per the exact
// flow documented in the backend's views_oauth.py docstring:
//   1. Redirect the browser here directly
//   2. Provider redirects back to our own /auth/callback/<provider> with ?code=
//   3. OAuthCallback.jsx POSTs that code to the backend callback endpoint

let publicClientIds = { google: "", github: "" }

export function setPublicOAuthIds(ids) {
  publicClientIds = { google: ids?.google || "", github: ids?.github || "" }
}

const googleClientId = () => import.meta.env.VITE_GOOGLE_CLIENT_ID || publicClientIds.google || ""
const githubClientId = () => import.meta.env.VITE_GITHUB_CLIENT_ID || publicClientIds.github || ""

const looksConfigured = (id) =>
  Boolean(id) && id.length >= 10 && !/dummy|placeholder|your[-_]|example|changeme/i.test(id)

export const hasGoogleClientId = () => looksConfigured(googleClientId())
export const hasGithubClientId = () => looksConfigured(githubClientId())

export function getRedirectUri(provider) {
  return `${window.location.origin}/auth/callback/${provider}`
}

export function getGoogleAuthUrl() {
  const clientId = googleClientId() || "google-oauth-client"
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: getRedirectUri("google"),
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    prompt: "select_account",
  })
  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`
}

export function getGithubAuthUrl() {
  const clientId = githubClientId() || "github-oauth-client"
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: getRedirectUri("github"),
    scope: "read:user user:email",
  })
  return `https://github.com/login/oauth/authorize?${params.toString()}`
}
