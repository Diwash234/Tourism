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

export function getRedirectUri(provider) {
  return `${window.location.origin}/auth/callback/${provider}`
}

// --- OAuth CSRF protection (state parameter) -------------------------
// A random state is generated before the redirect, stored in
// sessionStorage, sent to the provider, and verified when the provider
// redirects back (OAuthCallback.jsx). Without it, an attacker could
// complete their own OAuth flow and trick a victim's browser into logging
// into the attacker's account (login CSRF).
export function generateOAuthState(provider) {
  const bytes = new Uint8Array(24)
  crypto.getRandomValues(bytes)
  const state = Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("")
  try {
    sessionStorage.setItem(`oauth_state_${provider}`, state)
  } catch {
    /* private mode with sessionStorage disabled: state check is skipped */
  }
  return state
}

export function consumeOAuthState(provider, returnedState) {
  /** Returns true when the returned state matches the stored one.
   *  When no state was stored (e.g. sessionStorage unavailable) we cannot
   *  verify — callers treat that as "unverifiable" and refuse the login. */
  try {
    const expected = sessionStorage.getItem(`oauth_state_${provider}`)
    sessionStorage.removeItem(`oauth_state_${provider}`)
    return Boolean(expected) && expected === returnedState
  } catch {
    return false
  }
}

export function isProviderConfigured(provider) {
  const clientId =
    provider === "google"
      ? import.meta.env.VITE_GOOGLE_CLIENT_ID
      : import.meta.env.VITE_GITHUB_CLIENT_ID
  return Boolean(clientId)
}

export function getGoogleAuthUrl() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
  const params = new URLSearchParams({
    client_id: clientId || "",
    redirect_uri: getRedirectUri("google"),
    response_type: "code",
    scope: "openid email profile",
    access_type: "offline",
    // select_account makes Google show the full account chooser (every
    // Google account signed in on this phone/desktop browser) instead of
    // silently reusing the last-used account.
    prompt: "select_account",
    state: generateOAuthState("google"),
  })
  return `https://accounts.google.com/o/oauth2/v2/auth?${params.toString()}`
}

export function getGithubAuthUrl() {
  const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID
  const params = new URLSearchParams({
    client_id: clientId || "",
    redirect_uri: getRedirectUri("github"),
    scope: "read:user user:email",
    state: generateOAuthState("github"),
  })
  return `https://github.com/login/oauth/authorize?${params.toString()}`
}