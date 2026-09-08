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
    <footer className="bg-slate-950 text-emerald-100 mt-16 border-t border-emerald-500/30">
      <div className="h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-400" />

      {showBlock("symbols") && <div className="container-app py-8 border-b border-emerald-900/60">
        <div className="grid grid-cols-4 md:grid-cols-8 gap-3 sm:gap-5">
          {NATIONAL_ITEMS.map((item) => (
            <div
              key={item.title}
              className="flex flex-col items-center text-center"
            >
              <img
                src={item.image}
                alt={item.title}
                loading="lazy"
                className="
                  w-14
                  h-14
                  rounded-full
                  object-cover
                  border-2
                  border-emerald-400/50
                "
              />
              <span className="text-xs mt-2 text-emerald-200 font-medium">
                {item.title}
              </span>
            </div>
          ))}
        </div>

        <div className="mt-6 flex flex-col sm:flex-row justify-between items-center gap-3">
          <Link
            to="/discover-nepal"
            className="px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs shadow flex items-center justify-center gap-2 text-center transition-transform hover:scale-105"
          >
            <FiBookOpen size={16} /> See More — Explore All 26 National Symbols & Country Profile ➔
          </Link>

          <p className="text-sm italic text-emerald-400 font-semibold">
            {copy("symbols", "body", "Discover Nepal — Beyond Everest")}
          </p>
        </div>
      </div>}

      <div className="container-app py-12 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
        {showBlock("explore") && (
          <div>
            <h4 className="text-emerald-400 font-bold mb-3 text-sm uppercase tracking-wider">{copy("explore", "title", "Explore")}</h4>
            <ul className="space-y-2 text-sm">
              {exploreLinks.map((item) => (
                <li key={item.route}><Link to={item.route} className="text-emerald-200 hover:text-white transition-colors">{item.label}</Link></li>
              ))}
            </ul>
          </div>
        )}

        {showBlock("provinces") && (
          <div>
            <h4 className="text-emerald-400 font-bold mb-3 text-sm uppercase tracking-wider">{copy("provinces", "title", "Provinces")}</h4>
            <ul className="space-y-2 text-sm">
              {PROVINCE_CITY_LINKS.map((province) => (
                <li key={province.name}>
                  <Link to={`/destinations?q=${encodeURIComponent(province.city)}`} className="text-emerald-200 hover:text-white transition-colors">{province.name}</Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        {showBlock("company") && (
          <div>
            <h4 className="text-emerald-400 font-bold mb-3 text-sm uppercase tracking-wider">{copy("company", "title", "Company")}</h4>
            <ul className="space-y-2 text-sm">
              {companyLinks.map((link) => (
                <li key={link.route}>
                  <Link to={link.route} className={link.bold ? "text-emerald-300 font-bold hover:text-white" : "text-emerald-200 hover:text-white transition-colors"}>{link.label}</Link>
                </li>
              ))}
            </ul>
            <div className="mt-4 text-xs space-y-1 text-emerald-300 font-medium">
              <p>🚓 Police:<a href="tel:100" className="text-white font-bold ml-1">100</a></p>
              <p>🚑 Ambulance:<a href="tel:102" className="text-white font-bold ml-1">102</a></p>
              <p>🔥 Fire:<a href="tel:101" className="text-white font-bold ml-1">101</a></p>
            </div>
          </div>
        )}

        {showBlock("contact") && (
          <div>
            <h4 className="text-emerald-400 font-bold mb-3 text-sm uppercase tracking-wider">{copy("contact", "title", "Contact")}</h4>
            <ul className="space-y-3 text-sm">
              <li className="flex gap-2 items-center text-emerald-200"><FiMapPin className="text-emerald-400" /> {contactAddress}</li>
              <li className="flex gap-2 items-center text-emerald-200"><FiMail className="text-emerald-400" /> {contactEmail}</li>
              <li className="flex gap-2 items-center text-emerald-200"><FiPhone className="text-emerald-400" /> {contactPhone}</li>
            </ul>
            <div className="flex gap-4 mt-5 text-lg text-emerald-300">
              {branding.facebook_url && <a href={branding.facebook_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors" aria-label="Facebook"><FiFacebook /></a>}
              {branding.instagram_url && <a href={branding.instagram_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors" aria-label="Instagram"><FiInstagram /></a>}
              {branding.twitter_url && <a href={branding.twitter_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors" aria-label="X or Twitter"><FiTwitter /></a>}
              {branding.youtube_url && <a href={branding.youtube_url} target="_blank" rel="noopener noreferrer" className="hover:text-white transition-colors" aria-label="YouTube"><FiYoutube /></a>}
            </div>
          </div>
        )}
      </div>

      {showBlock("newsletter") && (
        <div className="container-app pb-10">
          <div className="rounded-2xl border border-emerald-500/30 bg-emerald-900/40 p-6 flex flex-col md:flex-row md:items-center gap-4">
            <div className="mr-auto">
              <h4 className="text-emerald-300 font-bold text-sm uppercase tracking-wider">{copy("newsletter", "title", "Travel Newsletter")}</h4>
              <p className="text-sm text-emerald-200 mt-1">{copy("newsletter", "subtitle", "Trip ideas, festivals and safety updates — straight to your inbox.")}</p>
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
                className="rounded-xl bg-slate-900 border border-emerald-500/40 px-3 py-2 text-sm text-emerald-100 placeholder:text-emerald-200/50 focus:outline-none focus:ring-2 focus:ring-emerald-400 w-full md:w-64"
              />
              <button
                type="submit"
                disabled={newsletterBusy}
                className="rounded-xl bg-emerald-500 hover:bg-emerald-400 disabled:opacity-50 text-slate-950 font-bold text-sm px-4 py-2 whitespace-nowrap"
              >
                {newsletterBusy ? "Signing up…" : "Subscribe"}
              </button>
            </form>
          </div>
          {newsletterMessage && <p role="status" className="mt-2 text-sm font-bold text-emerald-300">{newsletterMessage}</p>}
        </div>
      )}

      {filteredExtras?.length > 0 && <div className="container-app pb-8 text-emerald-100"><CMSExtras sections={filteredExtras} /></div>}

      <div className="border-t border-emerald-900/60 py-4 text-center text-xs text-emerald-300">
        © {new Date().getFullYear()} {siteTitle}. {branding.footer_text || "All rights reserved."}
        <button type="button" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })} className="ml-4 font-bold text-emerald-400 hover:text-white hover:underline">Back to top</button>
      </div>
    </footer>
  );
};

export default Footer;