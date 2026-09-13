import { useEffect, useState } from "react"
import configApi from "../api/configApi"
import { useI18n } from "../i18n"

const caches = new Map()
const pending = new Map()
const listeners = new Map()
const fallback = { settings: {}, pages: [], navigation: [] }

export const invalidatePublicConfigCache = () => {
  caches.clear()
  listeners.forEach((set, l) => {
    load(l).then((data) => set.forEach((fn) => fn(data)))
  })
}

if (typeof window !== "undefined") {
  window.addEventListener("cms-updated", invalidatePublicConfigCache)
  // Cross-tab: another tab's publish writes localStorage; the `storage` event
  // fires in every other tab so the public site refreshes without a reload.
  window.addEventListener("storage", (e) => { if (e.key === "cms-updated-at") invalidatePublicConfigCache() })
}

export const notifyCmsUpdated = () => {
  try { localStorage.setItem("cms-updated-at", String(Date.now())) } catch { /* private-mode storage — ignore */ }
  window.dispatchEvent(new Event("cms-updated"))
}

const load = lang => {
  if (caches.has(lang)) return Promise.resolve(caches.get(lang))
  if (!pending.has(lang)) pending.set(lang, configApi.getPublicConfig(lang).then(({ data }) => {
    caches.set(lang, data); (listeners.get(lang) || new Set()).forEach(fn => fn(data)); return data
  }).catch(() => fallback).finally(() => pending.delete(lang)))
  return pending.get(lang)
}

function applyBranding(branding = {}) {
  const root = document.documentElement
  const vars = { "--brand-primary": branding.primary_color, "--brand-secondary": branding.secondary_color, "--brand-background": branding.background_color, "--brand-surface": branding.surface_color }
  Object.entries(vars).forEach(([key, value]) => value && root.style.setProperty(key, value))
  root.dataset.themePreset = branding.theme_preset || "himalayan"
  root.dataset.density = branding.density || "comfortable"
  // Legacy brand guard: any DB/backup that still carries the old platform
  // name is rendered as "Nepal Yatra" (spec: single brand everywhere).
  const dropLegacyBrand = (value) =>
    String(value || "").replace(/Digital Nepal Tourism( Platform)?/g, "Nepal Yatra")
  if (branding.site_title) document.title = dropLegacyBrand(branding.site_title)
  if (branding.favicon_url) {
    let icon = document.querySelector("link[rel='icon']")
    if (!icon) { icon = document.createElement("link"); icon.rel = "icon"; document.head.appendChild(icon) }
    icon.href = branding.favicon_url
  }
}

export default function usePublicConfig() {
  const { lang } = useI18n()
  const [data, setData] = useState(caches.get(lang) || fallback)
  useEffect(() => {
    const languageListeners = listeners.get(lang) || new Set(); listeners.set(lang, languageListeners); languageListeners.add(setData)
    const t = setTimeout(() => { setData(caches.get(lang) || fallback); load(lang).then(setData) }, 0)
    return () => { languageListeners.delete(setData); clearTimeout(t) }
  }, [lang])
  const branding = data.settings?.branding || {}
  useEffect(() => {
    const t = setTimeout(() => applyBranding(branding), 0)
    return () => clearTimeout(t)
  }, [branding])
  const pageOf = (key) => data.pages?.find(item => item.key === key)
  // Tolerant section lookup: exact key first, then a `page-` prefix-insensitive
  // match, so template rows like `page-intro` resolve for pages that read `intro`.
  const section = (page, key) => {
    const sections = pageOf(page)?.sections
    if (!sections) return undefined
    const exact = sections.find(item => item.key === key)
    if (exact) return exact
    const norm = (value) => String(value || "").replace(/^page-/, "")
    return sections.find(item => norm(item.key) === norm(key))
  }
  const pageCMS = (pageKey, knownKeys = []) => {
    const page = pageOf(pageKey)
    const managed = Boolean(page?.sections?.length)
    const block = (key) => section(pageKey, key)
    const showBlock = (key) => !managed || Boolean(block(key))
    const copy = (key, field, fallback) => block(key)?.[field] || fallback
    const extras = (page?.sections || []).filter(item => !knownKeys.includes(item.key))
    return { page, managed, block, showBlock, copy, extras }
  }
  return { ...data, branding, section, pageOf, pageCMS }
}
