import { useEffect, useState } from "react"
import { FiRadio, FiSave, FiZap } from "react-icons/fi"
import adminApi from "../../api/adminApi"
import useToast from "../../hooks/useToast"

/**
 * Phase 3: the single switch that upgrades navigation from the bundled
 * coordinate-based graph to street-level OSRM-protocol routes. Admins paste
 * an OSRM/OpenRouteService-compatible base URL (+ optional key); the panel
 * never echoes a stored secret in full and offers an honest connection test.
 */
export default function RoutingProviderPanel() {
  const { showToast } = useToast()
  const [state, setState] = useState({ configured: false, enabled: false, base_url: "", api_key_set: false, api_key_last4: "" })
  const [form, setForm] = useState({ enabled: false, base_url: "", api_key: "" })
  const [busy, setBusy] = useState(false)
  const [testing, setTesting] = useState(false)
  const [verdict, setVerdict] = useState(null)

  const load = async () => {
    try {
      const { data } = await adminApi.getRoutingProvider()
      setState(data)
      setForm((prev) => ({ enabled: Boolean(data.enabled), base_url: data.base_url || "", api_key: prev.api_key }))
    } catch {
      showToast("Could not load routing provider settings.", "error")
    }
  }

  useEffect(() => {
    const t = setTimeout(() => load(), 0)
    return () => clearTimeout(t)
  }, [])

  const save = async () => {
    setBusy(true)
    try {
      const payload = { enabled: form.enabled, base_url: form.base_url.trim() }
      if (form.api_key.trim()) payload.api_key = form.api_key.trim()
      const { data } = await adminApi.updateRoutingProvider(payload)
      setState(data)
      setForm((prev) => ({ ...prev, api_key: "" }))
      setVerdict(null)
      showToast("Routing provider saved. Routes now use it (street-level when reachable).", "success")
    } catch (error) {
      showToast(error?.response?.data?.detail || "Could not save routing provider.", "error")
    } finally {
      setBusy(false)
    }
  }

  const test = async () => {
    setTesting(true)
    setVerdict(null)
    try {
      const { data } = await adminApi.testRoutingProvider()
      setVerdict(data)
    } catch (error) {
      setVerdict({ ok: false, error: error?.response?.data?.detail || "Test request failed." })
    } finally {
      setTesting(false)
    }
  }

  return (
    <section className="card-base p-6 space-y-4" data-testid="routing-provider-panel">
      <header className="flex items-center gap-2">
        <FiRadio className="text-emerald-600" />
        <h3 className="font-black uppercase tracking-wider text-sm">Road Routing Provider</h3>
        <span className={`ml-auto text-[10px] font-black px-2 py-1 rounded-full ${state.enabled ? "bg-emerald-100 text-emerald-700" : "bg-slate-200 text-slate-600"}`}>
          {state.enabled ? "ACTIVE — street-level routes" : "Bundled graph (coordinate-based)"}
        </span>
      </header>
      <p className="text-xs text-slate-500 leading-relaxed">
        Connect an OSRM-protocol routing service (self-hosted OSRM, OpenRouteService-compatible
        endpoint, …) to upgrade turn-by-turn navigation from the bundled tourism graph to
        street-level directions with real road names. HTTPS only — HTTP endpoints are rejected.
        Until a provider is reachable, routes stay honestly labelled as coordinate-based.
      </p>

      <label className="flex items-center gap-2 text-xs font-bold">
        <input type="checkbox" checked={form.enabled} onChange={(e) => setForm((prev) => ({ ...prev, enabled: e.target.checked }))} />
        Enable provider routing
      </label>

      <div>
        <label className="block text-[11px] font-black uppercase tracking-wider text-slate-500 mb-1">Base URL</label>
        <input
          type="url"
          value={form.base_url}
          onChange={(e) => setForm((prev) => ({ ...prev, base_url: e.target.value }))}
          placeholder="https://router.example.org"
          className="input-base w-full"
        />
        <p className="text-[10px] text-slate-400 mt-1">
          The service is called as <code>{"{base}/route/v1/driving/{lng},{lat};{lng},{lat}"}</code> (OSRM contract).
        </p>
      </div>

      <div>
        <label className="block text-[11px] font-black uppercase tracking-wider text-slate-500 mb-1">
          API key {state.api_key_set ? `(stored ••••${state.api_key_last4} — leave blank to keep)` : "(optional)"}
        </label>
        <input
          type="password"
          value={form.api_key}
          onChange={(e) => setForm((prev) => ({ ...prev, api_key: e.target.value }))}
          placeholder={state.api_key_set ? "••••••••" : "Bearer token, if required"}
          className="input-base w-full"
          autoComplete="new-password"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={save} disabled={busy}
          className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-black uppercase tracking-wider disabled:opacity-50 flex items-center gap-2">
          <FiSave /> {busy ? "Saving…" : "Save provider"}
        </button>
        <button type="button" onClick={test} disabled={testing}
          className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-white text-xs font-black uppercase tracking-wider disabled:opacity-50 flex items-center gap-2">
          <FiZap /> {testing ? "Testing…" : "Test connection"}
        </button>
      </div>

      {verdict && (
        <p className={`text-xs font-bold rounded-xl px-3 py-2 ${verdict.ok ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`} role="status">
          {verdict.ok
            ? `Reachable — ${verdict.routes_count} route(s) returned in ${verdict.latency_ms} ms. Street-level routing is live.`
            : `Not reachable: ${verdict.error} — navigation keeps using the honestly-labelled bundled graph.`}
        </p>
      )}
    </section>
  )
}
