import { useState } from "react";
import { Link } from "react-router-dom";
import {
  FiFacebook,
  FiInstagram,
  FiTwitter,
  FiYoutube,
  FiMapPin,
  FiMail,
  FiPhone,
  FiBookOpen,
} from "react-icons/fi";

import { APP_NAME } from "../../utils/constants";
import usePublicConfig from "../../hooks/usePublicConfig";
import configApi from "../../api/configApi";
import { CMSExtras } from "../cms/CMSBlock";

import {
  FlagImg,
  MapImg,
  CowImg,
  DanpheImg,
  RhododendronImg,
  EmblemImg,
  TopiImg,
  StupaImg,
} from "../dashboard/NationalSymbols";

/*
 * Footer redesign (task-79 §33): one cohesive premium identity instead of
 * stacked color blocks.
 *   Navy  #07101F  = structure/background (deep Nepal-night)
 *   Teal  #19C7A5  = brand, links, accents
 *   Gold  #F5C542  = action/highlight only (small CTA)
 * plus a barely-there Himalayan silhouette and a subtle radial teal glow so
 * the footer connects to the dark page instead of fighting it.
 */

const PROVINCE_CITY_LINKS = [
  { name: "Koshi", city: "Biratnagar" },
  { name: "Madhesh", city: "Janakpur" },
  { name: "Bagmati", city: "Kathmandu" },
  { name: "Gandaki", city: "Pokhara" },
  { name: "Lumbini", city: "Butwal" },
  { name: "Karnali", city: "Surkhet" },
  { name: "Sudurpashchim", city: "Dhangadhi" },
];

const NATIONAL_ITEMS = [
  { image: FlagImg, title: "National Flag" },
  { image: MapImg, title: "Nepal Map" },
  { image: CowImg, title: "National Animal" },
  { image: DanpheImg, title: "Danphe Bird" },
  { image: RhododendronImg, title: "Lali Gurans" },
  { image: EmblemImg, title: "National Emblem" },
  { image: TopiImg, title: "Dhaka Topi" },
  { image: StupaImg, title: "Stupa" },
];

// Verified national emergency numbers (already used across the platform).
const EMERGENCY_NUMBERS = [
  { label: "Police", number: "100", icon: "🚓" },
  { label: "Ambulance", number: "102", icon: "🚑" },
  { label: "Fire", number: "101", icon: "🔥" },
];

const linkClass = "text-[#91A0B5] hover:text-[#19C7A5] transition-colors";
const headingClass = "text-[11px] font-bold uppercase tracking-[0.14em] text-[#19C7A5] mb-3";

const Footer = () => {
  const { branding, navigation, pageCMS } = usePublicConfig()
  const { showBlock, copy, extras } = pageCMS("footer", ["symbols", "explore", "provinces", "company", "contact", "newsletter"])
  const footerNav = (navigation || []).filter(item => item.location === "footer" && String(item.route || "").startsWith("/"))

  const filteredExtras = (extras || []).filter(
    (sec) =>
      sec?.key !== "tagline" &&
      sec?.title !== "Footer note" &&
      !sec?.body?.includes("Discover destinations, plan budgets")
  )

  const rawTitle = branding.site_title || APP_NAME
  const siteTitle = rawTitle.replace(/Digital Nepal Tourism Platform/g, "Nepal Yatra").replace(/Digital Nepal Tourism/g, "Nepal Yatra").replace(/Digital Nepal/g, "Nepal Yatra")

  const contactAddress = branding.contact_address || "Pokhara, Nepal"
  const contactEmail = branding.contact_email || "support@tourists.app"
  const contactPhone = branding.contact_phone || "+977-000-0000"

  // Footer links are admin-managed (navigation rows with location "footer");
  // the fallback keeps the column populated before any are created. The
  // Company column skips routes already shown in Explore so nothing doubles.
  const exploreLinks = footerNav.length
    ? footerNav
    : [
        { label: "Destinations", route: "/destinations" },
        { label: "Recommendations", route: "/recommendation" },
        { label: "Budget Estimator", route: "/budget-estimator" },
        { label: "Risk Alerts", route: "/risk-alerts" },
      ]
  const exploreRoutes = new Set(exploreLinks.map((item) => item.route))
  const companyLinks = [
    { label: "How It Works", route: "/how-it-works", bold: true },
    { label: "Customer Support", route: "/support", bold: true },
    { label: "About Us", route: "/about" },
    { label: "Contact", route: "/contact" },
    { label: "Privacy Policy", route: "/privacy" },
    { label: "Terms of Service", route: "/terms" },
    { label: "Emergency", route: "/emergency" },
  ].filter((link) => !exploreRoutes.has(link.route))

  // Newsletter signup (brief §6) — real backend store, message comes from
  // the API response, never faked.
  const [newsletterEmail, setNewsletterEmail] = useState("")
  const [newsletterBusy, setNewsletterBusy] = useState(false)
  const [newsletterMessage, setNewsletterMessage] = useState("")

  const handleNewsletter = async (e) => {
    e.preventDefault()
    if (newsletterBusy) return
    setNewsletterBusy(true)
    setNewsletterMessage("")
    try {
      const res = await configApi.subscribeNewsletter(newsletterEmail.trim())
      setNewsletterMessage(res.data?.message || "Subscribed — thank you!")
      setNewsletterEmail("")
    } catch (err) {
      setNewsletterMessage(err.response?.data?.detail || "Could not subscribe — please try again.")
    } finally {
      setNewsletterBusy(false)
    }
  }

  return (
    <footer
      className="relative mt-16 text-[#F5F7FA] overflow-hidden"
      style={{
        background:
          "radial-gradient(circle at 50% 0%, rgba(25, 199, 165, 0.08), transparent 45%), #07101F",
      }}
    >
      {/* Very subtle Himalayan silhouette — identity, not decoration noise */}
      <svg
        aria-hidden="true"
        viewBox="0 0 1440 220"
        preserveAspectRatio="none"
        className="pointer-events-none absolute bottom-0 left-0 w-full h-36 opacity-[0.045]"
      >
        <path
          fill="#F5F7FA"
          d="M0,220 L120,120 L210,175 L320,70 L420,165 L520,95 L640,180 L760,55 L880,170 L980,105 L1090,175 L1200,85 L1310,160 L1440,110 L1440,220 Z"
        />
      </svg>

      {showBlock("symbols") && (
        <div className="relative container-app py-9 border-b border-white/[0.08]">
          <p className="text-center text-[11px] font-bold uppercase tracking-[0.2em] text-[#19C7A5] mb-6">
            Discover Nepal
          </p>
          <div className="grid grid-cols-4 md:grid-cols-8 gap-3 sm:gap-5">
            {NATIONAL_ITEMS.map((item) => (
              <div key={item.title} className="flex flex-col items-center text-center">
                <img
                  src={item.image}
                  alt={item.title}
                  loading="lazy"
                  className="w-14 h-14 rounded-full object-cover border border-[rgba(25,199,165,0.35)]"
                />
                <span className="text-xs mt-2 text-[#91A0B5] font-medium">{item.title}</span>
              </div>
            ))}
          </div>

          <div className="mt-6 flex flex-col sm:flex-row justify-between items-center gap-3">
            {/* Gold is the action accent — kept deliberately small (§33 rule 3) */}
            <Link
              to="/discover-nepal"
              className="px-4 py-2 rounded-lg bg-[#F5C542] hover:bg-[#f7d06a] text-[#07101F] font-bold text-xs shadow transition-colors flex items-center gap-2"
            >
              <FiBookOpen size={14} /> Explore Nepal →
            </Link>
            <p className="text-sm italic text-[#91A0B5] font-medium">
              {copy("symbols", "body", "Discover Nepal — Beyond Everest")}
            </p>
          </div>
        </div>
      )}

      <div className="relative container-app py-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        {showBlock("explore") && (
          <div>
            <h4 className={headingClass}>{copy("explore", "title", "Explore")}</h4>
            <ul className="space-y-2 text-sm">
              {exploreLinks.map((item) => (
                <li key={item.route}>
                  <Link to={item.route} className={linkClass}>{item.label}</Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        {showBlock("provinces") && (
          <div>
            <h4 className={headingClass}>{copy("provinces", "title", "Provinces")}</h4>
            <ul className="space-y-2 text-sm">
              {PROVINCE_CITY_LINKS.map((province) => (
                <li key={province.name}>
                  <Link to={`/destinations?q=${encodeURIComponent(province.city)}`} className={linkClass}>
                    {province.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        {showBlock("company") && (
          <div>
            <h4 className={headingClass}>{copy("company", "title", "Company")}</h4>
            <ul className="space-y-2 text-sm">
              {companyLinks.map((link) => (
                <li key={link.route}>
                  <Link
                    to={link.route}
                    className={link.bold ? "text-[#F5F7FA] font-semibold hover:text-[#19C7A5] transition-colors" : linkClass}
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="space-y-6">
          {/* Emergency gets its own highlighted block with a warm accent —
              useful for tourists, never buried among company links (§33 §5) */}
          <div className="rounded-2xl border border-[rgba(248,113,113,0.25)] bg-[rgba(248,113,113,0.06)] p-4">
            <h4 className="text-[11px] font-bold uppercase tracking-[0.14em] text-[#FCA5A5] mb-3">Emergency</h4>
            <ul className="space-y-1.5 text-sm">
              {EMERGENCY_NUMBERS.map((item) => (
                <li key={item.label} className="flex items-center justify-between gap-3">
                  <span className="text-[#91A0B5]">
                    {item.icon} {item.label}
                  </span>
                  <a href={`tel:${item.number}`} className="font-bold text-white hover:text-[#FCA5A5] transition-colors">
                    {item.number}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {showBlock("contact") && (
            <div>
              <h4 className={headingClass}>{copy("contact", "title", "Contact")}</h4>
              <ul className="space-y-2.5 text-sm">
                <li className="flex gap-2 items-center text-[#91A0B5]"><FiMapPin className="text-[#19C7A5] shrink-0" /> {contactAddress}</li>
                <li className="flex gap-2 items-center text-[#91A0B5]"><FiMail className="text-[#19C7A5] shrink-0" /> {contactEmail}</li>
                <li className="flex gap-2 items-center text-[#91A0B5]"><FiPhone className="text-[#19C7A5] shrink-0" /> {contactPhone}</li>
              </ul>
              <div className="flex gap-4 mt-4 text-lg text-[#19C7A5]">
                {branding.facebook_url && <a href={branding.facebook_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors" aria-label="Facebook"><FiFacebook /></a>}
                {branding.instagram_url && <a href={branding.instagram_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors" aria-label="Instagram"><FiInstagram /></a>}
                {branding.twitter_url && <a href={branding.twitter_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors" aria-label="X or Twitter"><FiTwitter /></a>}
                {branding.youtube_url && <a href={branding.youtube_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors" aria-label="YouTube"><FiYoutube /></a>}
              </div>
            </div>
          )}
        </div>
      </div>

      {showBlock("newsletter") && (
        <div className="relative container-app pb-10">
          {/* Subtle teal-bordered panel — not a competing color block (§33 §2) */}
          <div
            className="rounded-2xl p-6 flex flex-col md:flex-row md:items-center gap-4"
            style={{ background: "rgba(25, 199, 165, 0.08)", border: "1px solid rgba(25, 199, 165, 0.25)" }}
          >
            <div className="mr-auto">
              <h4 className="text-[#19C7A5] font-bold text-sm uppercase tracking-wider">{copy("newsletter", "title", "Travel Insights")}</h4>
              <p className="text-sm text-[#91A0B5] mt-1">{copy("newsletter", "subtitle", "Trip ideas, festivals and safety updates — straight to your inbox.")}</p>
            </div>
            <form onSubmit={handleNewsletter} className="flex gap-2 w-full md:w-auto">
              <label htmlFor="footer-newsletter-email" className="sr-only">Email address</label>
              <input
                id="footer-newsletter-email"
                type="email"
                required
                value={newsletterEmail}
                onChange={(e) => setNewsletterEmail(e.target.value)}
                placeholder="you@example.com"
                className="rounded-xl bg-[#0B1728] border border-[rgba(255,255,255,0.12)] px-3 py-2 text-sm text-[#F5F7FA] placeholder:text-[#91A0B5]/70 focus:outline-none focus:ring-2 focus:ring-[#19C7A5] w-full md:w-64"
              />
              <button
                type="submit"
                disabled={newsletterBusy}
                className="rounded-xl bg-[#F5C542] hover:bg-[#f7d06a] disabled:opacity-50 text-[#07101F] font-bold text-sm px-4 py-2 whitespace-nowrap transition-colors"
              >
                {newsletterBusy ? "Signing up…" : "Subscribe"}
              </button>
            </form>
          </div>
          {newsletterMessage && <p role="status" className="mt-2 text-sm font-bold text-[#19C7A5]">{newsletterMessage}</p>}
        </div>
      )}

      {filteredExtras?.length > 0 && <div className="relative container-app pb-8 text-[#91A0B5]"><CMSExtras sections={filteredExtras} /></div>}

      {/* Simple bottom bar — a proper visual ending (§33 §9) */}
      <div className="relative border-t border-white/[0.08] py-4">
        <div className="container-app flex flex-col sm:flex-row items-center justify-between gap-2 text-xs text-[#91A0B5]">
          <p>© {new Date().getFullYear()} {siteTitle}. {branding.footer_text || "Made for exploring Nepal 🇳🇵"}</p>
          <div className="flex items-center gap-4">
            <Link to="/privacy" className={linkClass}>Privacy</Link>
            <Link to="/terms" className={linkClass}>Terms</Link>
            <button
              type="button"
              onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })}
              className="font-bold text-[#19C7A5] hover:text-white hover:underline"
            >
              Back to top
            </button>
          </div>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
