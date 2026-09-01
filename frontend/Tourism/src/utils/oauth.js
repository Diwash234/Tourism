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

export function getGoogleAuthUrl() {
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID
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
  const clientId = import.meta.env.VITE_GITHUB_CLIENT_ID
  const params = new URLSearchParams({
    client_id: clientId || "",
    redirect_uri: getRedirectUri("github"),
    scope: "read:user user:email",
  })
  return `https://github.com/login/oauth/authorize?${params.toString()}`
}