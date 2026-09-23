import axiosClient from "./axiosClient"

const authApi = {
  login: (payload) => axiosClient.post("/auth/login/", payload),

  register: (payload) => axiosClient.post("/auth/register/", payload),

  forgotPassword: (payload) =>
    axiosClient.post("/auth/forgot-password/", payload),

  resetPassword: (payload) =>
    axiosClient.post("/auth/reset-password/", payload),

  // NEW: password reset via 6-digit one-time code (alternative to the
  // emailed link). Request → backend sends the code by SMS (Twilio, when
  // the account has a phone + Twilio is configured) or email. Verify →
  // code + new password change the password in one step and revoke all
  // sessions for the account.
  resetPasswordOtpRequest: (email) =>
    axiosClient.post("/auth/reset-password/otp/request/", { email }),
  resetPasswordOtpVerify: (payload) =>
    axiosClient.post("/auth/reset-password/otp/verify/", payload),

  // FIX: verifyEmail was only in the legacy services/api.js — the
  // backend emails a /verify-email?token=... link, and without this
  // method (and the page that uses it) newly registered users could
  // never verify their email.
  verifyEmail: (token) => axiosClient.post("/auth/verify-email/", { token }),

  // NEW (Round 21): resend the email-verification link for an existing
  // UNVERIFIED account. No login required — this is the "activate
  // account" option shown on the login page. Backend:
  // views_auth.ResendVerificationByEmailView (rate-limited 1/60s per
  // address, specific error messages: email_not_found / already
  // verified / sent-recently).
  resendVerification: (email) => axiosClient.post("/auth/resend-verification/", { email }),

  refreshToken: (payload) =>
    axiosClient.post("/auth/token/refresh/", payload),

  // FIXED: was calling POST /auth/logout/ with NO body. The backend's
  // LogoutView requires `{ "refresh": "<token>" }` to blacklist it —
  // without it, every logout call returned 400 and the token was never
  // actually invalidated server-side.
  logout: () =>
    axiosClient.post("/auth/logout/", { refresh: localStorage.getItem("refresh") }),

  getCurrentUser: () => axiosClient.get("/auth/profile/"),

  // NEW: phone verification. IMPORTANT — this is NOT a "login with
  // phone OTP" flow. Checked views_auth.py directly: both endpoints
  // require IsAuthenticated. The OTP is auto-sent by the backend during
  // RegisterView if a phone_number was included at signup; these two
  // calls only verify/resend it for an ALREADY-LOGGED-IN user. There is
  // no backend support for logging in via phone/OTP instead of a
  // password.
  verifyPhone: (code) => axiosClient.post("/auth/verify-phone/", { code }),
  resendPhoneOtp: () => axiosClient.post("/auth/resend-phone-otp/"),

  // NEW: OAuth callbacks — matches views_oauth.py exactly, including
  // its own docstring's described frontend flow:
  //   1. Frontend redirects to the provider's OAuth consent screen
  //   2. Provider redirects back with ?code=...
  //   3. Frontend POSTs that code here
  //   4. Backend returns {access, refresh, user} — same shape as login()
  googleAuthCallback: (code, redirectUri) =>
    axiosClient.post("/auth/google/callback/", { code, redirect_uri: redirectUri }),

  githubAuthCallback: (code) =>
    axiosClient.post("/auth/github/callback/", { code }),
}

export default authApi