// Functional navigation test entry — bundled by esbuild and driven from
// scripts/nav-behavior-test.cjs inside jsdom. This imports the REAL
// components and the REAL sidebar store; nothing is re-implemented here.
import React from "react"
import { createRoot } from "react-dom/client"
import { MemoryRouter, Routes, Route } from "react-router-dom"
import { AuthProvider } from "../src/context/AuthContext"
import { ThemeProvider } from "../src/context/ThemeContext"
import Navbar from "../src/components/layout/Navbar"
import Sidebar from "../src/components/layout/Sidebar"
import AdminLayout from "../src/components/admin/AdminLayout"
import CookieConsentBanner from "../src/components/common/CookieConsentBanner"
import NearbyPlaces from "../src/pages/NearbyPlaces"
import DataExplorerPanel from "../src/components/admin/DataExplorerPanel"
import CategoryTranslationPanel from "../src/components/admin/CategoryTranslationPanel"
import { ToastProvider } from "../src/context/ToastContext"
import axiosClient from "../src/api/axiosClient"
import { invalidatePublicConfigCache } from "../src/hooks/usePublicConfig"

const NullPage = () => React.createElement("div", { id: "page-probe" }, "page")

// --- deterministic transport -------------------------------------------------
// jsdom has no reachable API, so requests currently reject and every consumer
// falls back to empty data. A custom axios adapter keeps that exact behaviour
// for everything except /config/public/, which serves a fixture tests control.
// The real hook, cache, interceptors and components all run for real.
let publicConfigFixture = { settings: {}, pages: [], navigation: [] }
let nearbyFixture = { results: [], count: 0, fail: false, failOnce: false }
let nearbyCalls = []
let searchFixture = []
let hotelFixture = { results: [], count: 0 }
let hotelCalls = []
let emergencyFixture = { hospitals: [], police: [], specialized_contacts: [], national_hotlines: [] }
let emergencyCalls = []
let adminDestinationCalls = []
let categoryFixture = []
let categoryCalls = []
let dataExplorerFixtures = {
  list: { results: [], count: 0, total_pages: 1, page: 1, columns: ["id", "name"] },
  detail: {},
}
axiosClient.defaults.adapter = async (config) => {
  const url = String(config.url || "")
  const ok = (data) => ({ data, status: 200, statusText: "OK", headers: {}, config, request: {} })
  if (url.includes("/config/public/")) {
    return ok(publicConfigFixture)
  }
  if (url.includes("/destinations/nearby/")) {
    nearbyCalls.push({ url, params: { ...config.params } })
    if (nearbyFixture.fail || nearbyFixture.failOnce) {
      if (nearbyFixture.failOnce) nearbyFixture = { ...nearbyFixture, failOnce: false }
      const err = new Error("stubbed nearby failure")
      err.config = config
      err.response = { status: 500, data: {} }
      throw err
    }
    const results = nearbyFixture.results
    return ok({
      count: typeof nearbyFixture.count === "number" ? nearbyFixture.count : results.length,
      total_pages: 1,
      current_page: 1,
      next: null,
      previous: null,
      results,
    })
  }
  if (url.includes("/hotels/nearby/")) {
    hotelCalls.push({ url, params: { ...config.params } })
    const results = hotelFixture.results
    return ok({
      count: typeof hotelFixture.count === "number" ? hotelFixture.count : results.length,
      results,
    })
  }
  if (url.includes("/emergency/nearby/")) {
    emergencyCalls.push({ url, params: { ...config.params } })
    return ok({
      location: { latitude: 0, longitude: 0, source: "coordinates" },
      radius_km: config.params?.radius_km ?? 25,
      counts: { hospitals_within_radius: emergencyFixture.hospitals.length },
      hospitals: emergencyFixture.hospitals,
      police: emergencyFixture.police,
      specialized_contacts: emergencyFixture.specialized_contacts,
      national_hotlines: emergencyFixture.national_hotlines,
      coverage_gap: false,
      notice: "",
    })
  }
  if (url.includes("/admin/data-explorer/")) {
    return ok(dataExplorerFixtures.list)
  }
  if (url.includes("/admin/destinations")) {
    const method = (config.method || "get").toLowerCase()
    if (method === "post" && !/\/admin\/destinations\/\d+/.test(url)) {
      adminDestinationCalls.push({ method, url, data: config.data })
      return ok({ id: 777, slug: "harness-created-place", message: "Destination created successfully" })
    }
    if (method === "delete") {
      adminDestinationCalls.push({ method, url })
      return ok({ message: "Destination archived; related records were retained", id: 77 })
    }
  }
  if (url.includes("/admin/destinations/")) {
    return ok(dataExplorerFixtures.detail)
  }
  if (url.includes("/categories/")) {
    const method = (config.method || "get").toLowerCase()
    categoryCalls.push({ method, url, data: config.data })
    if (method === "get") {
      return ok({
        count: categoryFixture.length,
        total_pages: 1,
        current_page: 1,
        next: null,
        previous: null,
        results: categoryFixture,
      })
    }
    return ok({})
  }
  if (url.includes("/destinations/")) {
    return ok({
      count: searchFixture.length,
      total_pages: 1,
      current_page: 1,
      next: null,
      previous: null,
      results: searchFixture,
    })
  }
  const err = new Error(`stubbed failure for ${config.url}`)
  err.config = config
  err.response = { status: 404, data: {} }
  throw err
}
export function setPublicConfigFixture(fixture) {
  publicConfigFixture = fixture
  invalidatePublicConfigCache()
}

// --- nearby fixtures + recording ---------------------------------------------
export function setNearbyFixture(f) {
  nearbyFixture = { results: [], count: 0, fail: false, failOnce: false, ...f }
  nearbyCalls = []
}
export function setSearchFixture(rows) {
  searchFixture = rows
}
export function getNearbyCalls() {
  return nearbyCalls
}
export function setHotelFixture(f) {
  hotelFixture = { results: [], count: 0, ...f }
  hotelCalls = []
}
export function getHotelCalls() {
  return hotelCalls
}
export function setEmergencyFixture(f) {
  emergencyFixture = { hospitals: [], police: [], specialized_contacts: [], national_hotlines: [], ...f }
  emergencyCalls = []
}
export function getEmergencyCalls() {
  return emergencyCalls
}
export function setDataExplorerFixtures(f) {
  dataExplorerFixtures = {
    list: { results: [], count: 0, total_pages: 1, page: 1, columns: ["id", "name"], ...(f.list || {}) },
    detail: f.detail || {},
  }
}

// jsdom has no geolocation — install a controllable stub on the navigator the
// component reads. "unsupported" models browsers without the API at all.
export function setGeolocation(mode, coords = {}) {
  const nav = globalThis.navigator
  if (mode === "unsupported") {
    Object.defineProperty(nav, "geolocation", { value: undefined, configurable: true })
    return
  }
  const stub = {
    getCurrentPosition(onSuccess, onError) {
      if (mode === "denied") {
        const err = new Error("User denied Geolocation")
        err.code = 1
        setTimeout(() => onError(err), 0)
      } else {
        setTimeout(() => onSuccess({ coords: { latitude: coords.lat, longitude: coords.lng } }), 0)
      }
    },
  }
  Object.defineProperty(nav, "geolocation", { value: stub, configurable: true })
}

export function mountDataExplorer() {
  const container = document.createElement("div")
  document.body.appendChild(container)
  const root = createRoot(container)
  React.act(() => {
    root.render(
      React.createElement(
        MemoryRouter, null,
        React.createElement(
          ToastProvider, null,
          React.createElement(DataExplorerPanel)
        )
      )
    )
  })
  return {
    container,
    unmount: () => React.act(() => root.render(null)),
  }
}

export function mountNearbyPage() {
  const container = document.createElement("div")
  document.body.appendChild(container)
  const root = createRoot(container)
  React.act(() => {
    root.render(
      React.createElement(
        MemoryRouter, { initialEntries: ["/nearby-places"] },
        React.createElement(
          AuthProvider, null,
          React.createElement(
            ToastProvider, null,
            React.createElement(NearbyPlaces)
          )
        )
      )
    )
  })
  return {
    container,
    unmount: () => React.act(() => root.render(null)),
  }
}

export function mountCookieBanner() {
  const container = document.createElement("div")
  document.body.appendChild(container)
  const root = createRoot(container)
  React.act(() => {
    root.render(
      React.createElement(MemoryRouter, null, React.createElement(CookieConsentBanner))
    )
  })
  return {
    container,
    unmount: () => React.act(() => root.render(null)),
  }
}

export function mountTravellerShell() {
  const container = document.createElement("div")
  document.body.appendChild(container)
  const root = createRoot(container)
  React.act(() => {
    root.render(
      React.createElement(
        MemoryRouter, { initialEntries: ["/destinations"] },
        React.createElement(
          AuthProvider, null,
          React.createElement(
            ThemeProvider, null,
            React.createElement(Navbar),
            React.createElement(Sidebar)
          )
        )
      )
    )
  })
  return {
    container,
    unmount: () => React.act(() => root.render(null)),
  }
}

export function mountAdminShell() {
  const container = document.createElement("div")
  document.body.appendChild(container)
  const root = createRoot(container)
  React.act(() => {
    root.render(
      React.createElement(
        MemoryRouter, { initialEntries: ["/admin?section=reports"] },
        React.createElement(
          AuthProvider, null,
          React.createElement(
            ThemeProvider, null,
            React.createElement(
              Routes, null,
              React.createElement(
                Route, { path: "/admin", element: React.createElement(AdminLayout) },
                React.createElement(Route, { index: true, element: React.createElement(NullPage) })
              )
            )
          )
        )
      )
    )
  })
  return {
    container,
    unmount: () => React.act(() => root.render(null)),
  }
}

export function setCategoryFixture(rows) {
  categoryFixture = rows
  categoryCalls = []
}

export function getAdminDestinationCalls() {
  return adminDestinationCalls
}

export function getCategoryCalls() {
  return categoryCalls
}

export function mountCategoryPanel() {
  const container = document.createElement("div")
  document.body.appendChild(container)
  const root = createRoot(container)
  React.act(() => {
    root.render(
      React.createElement(
        MemoryRouter, null,
        React.createElement(
          ToastProvider, null,
          React.createElement(CategoryTranslationPanel)
        )
      )
    )
  })
  return {
    container,
    unmount: () => React.act(() => root.render(null)),
  }
}

export const act = React.act
