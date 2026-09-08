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
import axiosClient from "../src/api/axiosClient"
import { invalidatePublicConfigCache } from "../src/hooks/usePublicConfig"

const NullPage = () => React.createElement("div", { id: "page-probe" }, "page")

// --- deterministic transport -------------------------------------------------
// jsdom has no reachable API, so requests currently reject and every consumer
// falls back to empty data. A custom axios adapter keeps that exact behaviour
// for everything except /config/public/, which serves a fixture tests control.
// The real hook, cache, interceptors and components all run for real.
let publicConfigFixture = { settings: {}, pages: [], navigation: [] }
axiosClient.defaults.adapter = async (config) => {
  if (String(config.url || "").includes("/config/public/")) {
    return { data: publicConfigFixture, status: 200, statusText: "OK", headers: {}, config, request: {} }
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

export const act = React.act
