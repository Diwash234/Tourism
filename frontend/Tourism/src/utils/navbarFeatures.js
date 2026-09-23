/**
 * Header & Navbar feature flags (CMS brief §5).
 *
 * Stored as the public `navbar_features` SiteSetting row and served through
 * the public config, so an admin toggle applies to the live site with no
 * rebuild. Every flag DEFAULTS TO TRUE: a missing row or missing key must
 * never hide a feature (backwards compatible with every existing deploy).
 */

export const NAVBAR_FEATURES = [
  { key: "search", label: "Search bar", description: "Destination & safety search in the header" },
  { key: "language_switcher", label: "Language switcher", description: "English / नेपाली / हिन्दी picker" },
  { key: "profile", label: "Profile menu", description: "Signed-in account menu with dashboard access" },
  { key: "notifications", label: "Notifications bell", description: "Shortcut to the notifications page" },
  { key: "theme_toggle", label: "Theme toggle", description: "Light / dark mode switch" },
]

export const resolveNavbarFeatures = (value) => {
  const source = value && typeof value === "object" ? value : {}
  const resolved = {}
  NAVBAR_FEATURES.forEach(({ key }) => {
    resolved[key] = source[key] !== false
  })
  return resolved
}
