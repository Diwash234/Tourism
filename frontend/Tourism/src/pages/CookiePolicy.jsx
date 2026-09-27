import { Link } from "react-router-dom"
import LegalPage, { LegalContact, LegalTable } from "../components/legal/LegalPage"
import useCookieChoice from "../hooks/useCookieChoice"
import { openCookieSettings } from "../utils/cookieConsent"

// Keep in sync with the code: every key below is written somewhere in src/.
// If you add browser storage, list it here in the same change.
const ESSENTIAL = [
  ["django_language (cookie)", "Remembers the language you chose so the server replies in it", "1 year"],
  ["sessionid, csrftoken (cookies)", "Staff sign-in and form protection on the admin site only", "Until sign-out / 1 year"],
  ["access, refresh, user", "Keep you signed in", "Until you sign out"],
  ["tourism_cookie_consent", "Remembers your choice on this banner", "Until you clear it"],
  ["tourism_lang, tourism_preferred_language, translation_provider", "Language and translation preferences", "Until you clear it"],
  ["ny_theme, ny_sidebar_open", "Light or dark theme and whether the side menu is open", "Until you clear it"],
  ["tourism_currency, tourism_nationality", "Currency and nationality used for prices and visa rules", "Until you clear it"],
  ["nepal_yatra_user_preferences, tourism_trip_basket", "Interests and places you picked while planning", "Until you clear it"],
  ["np-nav-cached-routes, nepal_nav_offline_packs_v1, ny.emergency.national_hotlines.v1", "Routes, map areas and emergency numbers saved for offline use", "Until you clear it"],
  ["cms-updated-at", "Knows when page content changed so it can refresh", "Until you clear it"],
  ["nav_itinerary_stops, nepal_yatra_submission_receipt, phone_verified_this_session (session storage)", "Short-lived state for the current tab", "Until the tab closes"],
  ["Service worker cache", "Stores pages and files so the site opens offline", "Until the site updates or you clear it"],
]

const sections = [
  {
    id: "summary", title: "Summary",
    body: (
      <>
        <p>Nepal Yatra does not use analytics, advertising or social-media tracking cookies, and does not share browsing data with advertisers.</p>
        <p>We use a small amount of browser storage that the site needs to work. Most of it is &quot;local storage&quot; rather than cookies, but we list it all here because it serves the same purpose.</p>
      </>
    ),
  },
  {
    id: "essential", title: "Storage the site needs",
    body: (
      <>
        <p>These items are set only by Nepal Yatra and never leave your device except the language cookie and the sign-in token, which are sent to our own server. They are needed for features you use, so they are not switched off by the banner.</p>
        <LegalTable head={["Name", "Purpose", "Kept"]} rows={ESSENTIAL} />
      </>
    ),
  },
  {
    id: "videos", title: "Embedded videos (your choice)",
    body: (
      <>
        <p>Some pages can include a YouTube or Vimeo video. Those players are run by their companies and may set their own cookies or storage when they load. Until you choose &quot;Allow videos&quot;, each video shows a placeholder and nothing is requested from YouTube or Vimeo. You can also play a single video without changing your choice.</p>
        <p>When a video does load we use YouTube&apos;s privacy-enhanced mode (youtube-nocookie.com) and ask Vimeo not to track (dnt=1).</p>
        <VideoChoice />
      </>
    ),
  },
  {
    id: "other-requests", title: "Other services your browser contacts",
    body: <p>Maps load tiles from OpenStreetMap and, for the satellite view, Esri. Destination photos load from Wikimedia Commons. These requests share your IP address with those services, as any image request does, but we do not ask them to set cookies. See the <Link className="ny-legal-link" to="/privacy-policy#sharing">Privacy Policy</Link> for the full list.</p>,
  },
  {
    id: "control", title: "How to control storage",
    body: <p>You can clear cookies and site data in your browser settings at any time. Clearing it signs you out and resets your preferences and offline data.</p>,
  },
  { id: "contact", title: "Contact", body: <LegalContact /> },
]

function VideoChoice() {
  const choice = useCookieChoice()
  const status = choice === null ? "You have not chosen yet." : choice.media ? "Embedded videos are allowed." : "Embedded videos are blocked."
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-[var(--ny-radius-md)] bg-[var(--ny-bg)] p-4">
      <p className="text-sm font-semibold text-[var(--ny-text)]" aria-live="polite">{status}</p>
      <button type="button" onClick={openCookieSettings} className="ny-btn ny-btn-secondary min-h-11 px-4 text-sm">Change video choice</button>
    </div>
  )
}

export default function CookiePolicy() {
  return (
    <LegalPage
      pageKey="cookie-policy"
      title="Cookie Policy"
      path="/cookie-policy"
      intro={<p>This page lists every cookie and piece of browser storage Nepal Yatra uses, what it is for and how long it stays.</p>}
      sections={sections}
    />
  )
}
