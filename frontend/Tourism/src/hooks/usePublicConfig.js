import { useEffect, useState } from "react"
import configApi from "../api/configApi"
import { useI18n } from "../i18n"

const caches = new Map()
const pending = new Map()
const listeners = new Map()
const fallback = { settings: {}, pages: [], navigation: [] }
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
  if (branding.site_title) document.title = branding.site_title
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
    setData(caches.get(lang) || fallback); load(lang).then(setData)
    return () => languageListeners.delete(setData)
  }, [lang])
  const branding = data.settings?.branding || {}
  useEffect(() => applyBranding(branding), [branding])
  const section = (page, key) => data.pages?.find(item => item.key === page)?.sections?.find(item => item.key === key)
  return { ...data, branding, section }
}
