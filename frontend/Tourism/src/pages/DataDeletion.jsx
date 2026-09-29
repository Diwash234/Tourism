import { useState } from "react"
import { Link } from "react-router-dom"
import LegalPage, { LegalContact } from "../components/legal/LegalPage"
import useAuth from "../hooks/useAuth"
import authApi from "../api/authApi"

function DeleteAccountForm() {
  const { user, isAuthenticated, logout } = useAuth()
  const [secret, setSecret] = useState("")
  const [understood, setUnderstood] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null) // { message, field }
  const [done, setDone] = useState(null)

  if (done) {
    return (
      <div role="status" className="rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] bg-[var(--ny-bg)] p-4 text-[var(--ny-text)]">
        <p className="font-bold">Your account has been deleted and you have been signed out.</p>
        <p className="mt-1 text-sm text-[var(--ny-text-secondary)]">{done}</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return (
      <div className="rounded-[var(--ny-radius-md)] bg-[var(--ny-bg)] p-4">
        <p className="text-[var(--ny-text)]">Sign in to delete your account. We ask you to sign in so nobody else can delete it.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Link to="/login" state={{ from: { pathname: "/data-deletion" } }} className="ny-btn ny-btn-primary min-h-11 px-4">Sign in</Link>
          <Link to="/forgot-password" className="ny-btn ny-btn-secondary min-h-11 px-4">Forgot your password?</Link>
        </div>
      </div>
    )
  }

  if (user?.is_superuser) {
    return <p className="rounded-[var(--ny-radius-md)] bg-[var(--ny-bg)] p-4 text-[var(--ny-text)]">Super administrator accounts cannot be deleted here. Ask another administrator to take over ownership first.</p>
  }

  const usesPassword = user?.has_password !== false
  const field = usesPassword ? "password" : "confirm_email"
  const inputId = "delete-account-secret"
  const errorId = "delete-account-error"

  const submit = async (event) => {
    event.preventDefault()
    setError(null)
    if (!understood) { setError({ message: "Tick the box to confirm you understand this cannot be undone.", field: "understood" }); return }
    setBusy(true)
    try {
      const { data } = await authApi.deleteAccount({ [field]: secret })
      // The server has already revoked the tokens; clear this browser's
      // session before confirming, so the page never shows a stale sign-in.
      await logout()
      setDone(data?.kept || "")
    } catch (err) {
      const body = err?.response?.data || {}
      setError({ message: body.detail || "Your account could not be deleted. Please try again.", field: body.field || null })
    } finally {
      setBusy(false)
    }
  }

  return (
    <form onSubmit={submit} noValidate className="space-y-4 rounded-[var(--ny-radius-md)] border border-[var(--ny-border)] p-4">
      <p className="text-sm text-[var(--ny-text)]">Signed in as <strong>{user?.email}</strong></p>
      <div>
        <label htmlFor={inputId} className="block text-sm font-bold text-[var(--ny-text)]">
          {usesPassword ? "Your password" : "Type your account email to confirm"}
        </label>
        <input
          id={inputId}
          type={usesPassword ? "password" : "email"}
          autoComplete={usesPassword ? "current-password" : "email"}
          required
          value={secret}
          onChange={(e) => setSecret(e.target.value)}
          aria-invalid={error?.field === field || undefined}
          aria-describedby={error ? errorId : undefined}
          className="input-field mt-1"
        />
        {!usesPassword && <p className="mt-1 text-xs text-[var(--ny-text-secondary)]">You signed in with Google or GitHub, so there is no password to enter.</p>}
      </div>
      <label className="flex items-start gap-2 text-sm text-[var(--ny-text)]">
        <input
          type="checkbox"
          checked={understood}
          onChange={(e) => setUnderstood(e.target.checked)}
          aria-invalid={error?.field === "understood" || undefined}
          className="mt-1 h-4 w-4"
        />
        <span>I understand my account and the data listed above will be deleted and this cannot be undone.</span>
      </label>
      {error && <p id={errorId} role="alert" className="text-sm font-semibold text-[var(--ny-danger)]">{error.message}</p>}
      <button type="submit" disabled={busy || !secret} className="ny-btn ny-btn-danger min-h-11 px-5">
        {busy ? "Deleting…" : "Delete my account"}
      </button>
    </form>
  )
}

const sections = [
  {
    id: "deleted", title: "What is deleted",
    body: (
      <ul className="list-disc space-y-1 pl-5">
        <li>Your name, email address, phone number, password, profile photo, bio and saved location.</li>
        <li>Trip plans, budgets, saved routes, favourites, visit history and recommendation settings.</li>
        <li>Companion and document details, trusted contacts and recorded trip locations. Active trip shares stop working.</li>
        <li>Travel assistant conversations, notifications, notification settings and push tokens.</li>
        <li>Your newsletter subscription, if it used the same email address.</li>
      </ul>
    ),
  },
  {
    id: "kept", title: "What is kept, and why",
    body: (
      <ul className="list-disc space-y-1 pl-5">
        <li><strong className="text-[var(--ny-text)]">Booking requests</strong> stay with the provider&apos;s records, with your name, email, phone and notes removed.</li>
        <li><strong className="text-[var(--ny-text)]">SOS alerts</strong> stay for safety follow-up (730 days after they are resolved), no longer linked to your name.</li>
        <li><strong className="text-[var(--ny-text)]">Security logs</strong> stay for their retention period to protect the service. Older entries can include your email and IP address.</li>
        <li><strong className="text-[var(--ny-text)]">Published reviews and approved place suggestions</strong> stay, shown as &quot;Deleted User&quot;. Ask us if you want them removed too.</li>
      </ul>
    ),
  },
  {
    id: "delete", title: "Delete your account",
    body: <DeleteAccountForm />,
  },
  {
    id: "other", title: "Other requests",
    body: (
      <>
        <p>To only stop newsletter emails, use the <Link className="ny-legal-link" to="/unsubscribe">unsubscribe page</Link>. If you cannot sign in, or want a copy of your information or specific content removed, contact us:</p>
        <LegalContact />
      </>
    ),
  },
]

export default function DataDeletion() {
  return (
    <LegalPage
      pageKey="data-deletion"
      title="Delete your account and data"
      path="/data-deletion"
      intro={<p>You can delete your Nepal Yatra account yourself at any time. Deletion happens straight away and cannot be undone. See the <Link className="ny-legal-link" to="/privacy-policy">Privacy Policy</Link> for how your information is used.</p>}
      sections={sections}
    />
  )
}
