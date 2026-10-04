// Pagination behaviour test entry: renders the REAL DestinationList (real
// Pagination, real router/URL sync) against a deterministic fake catalogue API
// shaped like /api/v1/destinations/ (4,603 places, 12 per page, 384 pages).
import React from "react"
import { createRoot } from "react-dom/client"
import { MemoryRouter, useLocation } from "react-router-dom"
import { AuthProvider } from "../src/context/AuthContext"
import { ThemeProvider } from "../src/context/ThemeContext"
import { ToastProvider } from "../src/context/ToastContext"
import DestinationList from "../src/pages/destinations/DestinationList"
import axios from "axios"
import axiosClient from "../src/api/axiosClient"

export const TOTAL = 4603
export const PER_PAGE = 12
export const calls = []
let LATENCY_MS = 0
export const setLatency = (ms) => { LATENCY_MS = ms }

const stubAdapter = async (config) => {
  const url = String(config.url || "")
  const params = { ...(config.params || {}) }
  const respond = (data, status = 200) => ({ data, status, statusText: "OK", headers: {}, config, request: {} })
  if (/\/destinations\/?$/.test(url.split("?")[0])) {
    const page = Number(params.page || 1)
    const size = Number(params.limit || params.page_size || PER_PAGE)
    if (params.featured) return respond({ results: [], count: 0, total_pages: 1, current_page: 1 })
    calls.push({ page, size, params })
    const pages = Math.ceil(TOTAL / size)
    if (LATENCY_MS) await new Promise((r) => setTimeout(r, LATENCY_MS))
    if (page < 1 || page > pages) {
      const err = new Error("Invalid page"); err.response = respond({ error: { code: "not_found" } }, 404); err.config = config
      throw err
    }
    const start = (page - 1) * size
    const n = Math.min(size, TOTAL - start)
    return respond({
      count: TOTAL, total_pages: pages, current_page: page, next: null, previous: null,
      results: Array.from({ length: n }, (_, i) => ({
        id: start + i + 1, slug: `place-${start + i + 1}`, name: `Place ${start + i + 1}`,
        district: "Kaski", province: "Gandaki", cover_image_url: "", latitude: 28.2, longitude: 84,
      })),
    })
  }
  return respond({ results: [], count: 0, settings: {}, pages: [], navigation: [] })
}
axiosClient.defaults.adapter = stubAdapter
axios.defaults.adapter = stubAdapter

let currentLocation = "/"
function LocationProbe() {
  const loc = useLocation()
  currentLocation = loc.pathname + loc.search
  return null
}
export const getLocation = () => currentLocation

export function mount(container, initialEntry = "/destinations") {
  const root = createRoot(container)
  root.render(
    <MemoryRouter initialEntries={[initialEntry]}>
      <ThemeProvider><AuthProvider><ToastProvider>
        <LocationProbe />
        <DestinationList />
      </ToastProvider></AuthProvider></ThemeProvider>
    </MemoryRouter>
  )
  return root
}
