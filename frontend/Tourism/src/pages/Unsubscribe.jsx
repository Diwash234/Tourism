import { useEffect, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import Breadcrumbs from "../components/common/Breadcrumbs"
import configApi from "../api/configApi"
import CMSPageIntro from "../components/cms/CMSPageIntro"

/**
 * One-click unsubscribe from the travel-notes newsletter. A signed ?token=
 * (from the link in each email) is processed on arrival; otherwise the
 * visitor types their address. The reply never reveals whether an address
 * was subscribed.
 */
export default function Unsubscribe() {
  const [params] = useSearchParams()
  const token = params.get("token") || ""
  const [email, setEmail] = useState("")
  const [state, setState] = useState(token ? "working" : "idle") // idle | working | done | error
  const [message, setMessage] = useState("")
  const sentToken = useRef("")

  const send = async (body) => {
    setState("working")
    try {
      const { data } = await configApi.unsubscribeNewsletter(body)
      setMessage(data?.message || "Done.")
      setState("done")
    } catch (err) {
      setMessage(err?.response?.data?.detail || "Something went wrong. Please try again.")
      setState("error")
    }
  }

  useEffect(() => {
    if (!token || sentToken.current === token) return
    sentToken.current = token
    // eslint-disable-next-line react-hooks/set-state-in-effect -- one network call per token
    send({ token })
  }, [token])

  return (
    <div className="container-app py-8">
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Unsubscribe", to: "/unsubscribe" }]} />
      <section className="ny-reading ny-card mt-4 max-w-xl p-6 text-[var(--ny-text)] sm:p-8" aria-labelledby="unsub-title">
        <h1 id="unsub-title" className="text-2xl font-black tracking-tight">Unsubscribe from travel notes</h1>
        <p className="mt-2 text-sm leading-6 text-[var(--ny-text-secondary)]">This stops newsletter emails only. Account and booking emails are not affected.</p>

        <div aria-live="polite" className="mt-4">
          {state === "working" && <p className="text-sm">Unsubscribing…</p>}
          {state === "done" && <p role="status" className="rounded-[var(--ny-radius-md)] bg-[var(--ny-soft-green)] p-3 text-sm font-semibold">{message}</p>}
          {state === "error" && <p role="alert" className="text-sm font-semibold text-[var(--ny-danger)]">{message}</p>}
        </div>

        {state !== "done" && state !== "working" && (
          <form
            className="mt-4 flex flex-col gap-3 sm:flex-row sm:items-end"
            onSubmit={(e) => { e.preventDefault(); send({ email }) }}
          >
            <div className="flex-1">
              <label htmlFor="unsub-email" className="block text-sm font-bold">Email address</label>
              <input id="unsub-email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} className="input-field mt-1" />
            </div>
            <button type="submit" className="ny-btn ny-btn-primary min-h-11 px-5" disabled={!email.trim()}>Unsubscribe</button>
          </form>
        )}

        <p className="mt-6 text-sm text-[var(--ny-text-secondary)]">
          Want to delete your whole account instead? Go to <Link className="ny-legal-link" to="/data-deletion">delete your account and data</Link>.
        </p>
      </section>
      <CMSPageIntro pageKey="unsubscribe" />
    </div>
  )
}
