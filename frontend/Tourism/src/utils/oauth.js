// Builds the provider's OAuth "authorize" URL client-side:
// Buttons are only rendered when a real client ID is configured
// (SocialLoginButtons); without one there is no social login.

let publicClientIds = { google: "", github: "" }

export function setPublicOAuthIds(ids) {
  publicClientIds = { google: ids?.google || "", github: ids?.github || "" }
}

const googleClientId = () => import.meta.env.VITE_GOOGLE_CLIENT_ID || publicClientIds.google || ""
const githubClientId = () => import.meta.env.VITE_GITHUB_CLIENT_ID || publicClientIds.github || ""

const looksConfigured = (id) =>
  Boolean(id) && id.length >= 10 && !/dummy|placeholder|your[-_]|example|changeme|google-oauth-client|github-oauth-client/i.test(id)

export const hasGoogleClientId = () => looksConfigured(googleClientId())
export const hasGithubClientId = () => looksConfigured(githubClientId())

export function getRedirectUri(provider) {
  return `${window.location.origin}/auth/callback/${provider}`
}

export function getGoogleAuthUrl() {
  const clientId = googleClientId()
  if (!looksConfigured(clientId)) {
    return ""
  }
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
  const clientId = githubClientId()
  if (!looksConfigured(clientId)) {
    return ""
  }
  const params = new URLSearchParams({
    client_id: clientId,
    redirect_uri: getRedirectUri("github"),
    scope: "read:user user:email",
  })
  return `https://github.com/login/oauth/authorize?${params.toString()}`
}
