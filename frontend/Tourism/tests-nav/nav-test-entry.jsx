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

const NullPage = () => React.createElement("div", { id: "page-probe" }, "page")

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
