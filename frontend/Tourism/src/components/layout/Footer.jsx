import { useState } from "react"
import useAuth from "../../hooks/useAuth"
import { Link } from "react-router-dom"
import { FiArrowRight, FiFacebook, FiGlobe, FiInstagram, FiMail, FiMapPin, FiPhone, FiTwitter, FiYoutube } from "react-icons/fi"
import { APP_NAME } from "../../utils/constants"
import usePublicConfig from "../../hooks/usePublicConfig"
import configApi from "../../api/configApi"
import { CMSExtras } from "../cms/CMSBlock"
import { EmblemImg, StupaImg, TopiImg, FlagImg, MapImg, CowImg, DanpheImg, RhododendronImg } from "../dashboard/NationalSymbols"

const PROVINCES = ["Koshi", "Madhesh", "Bagmati", "Gandaki", "Lumbini", "Karnali", "Sudurpashchim"]
const PUBLIC_FOOTER_PATHS = new Set([
  "/", "/destinations", "/recommendation", "/gallery", "/compare", "/explore-map", "/discover-nepal",
  "/itinerary", "/budget-estimator", "/hotels/search", "/emergency", "/risk-alerts", "/navigation",
  "/distances", "/language", "/translation", "/nearby-places", "/packages", "/guides", "/guide-portal",
  "/tourism-jobs", "/guide-bookings", "/collaborate", "/chatbot", "/travel", "/about", "/contact", "/support", "/how-it-works",
])

const NATIONAL_SYMBOLS = [
  ["National Flag", FlagImg],
  ["Nepal Map", MapImg],
  ["National Animal", CowImg],
  ["Danphe", DanpheImg],
  ["Lali Gurans", RhododendronImg],
  ["National Emblem", EmblemImg],
  ["Dhaka Topi", TopiImg],
  ["Stupa", StupaImg],
]

const DEFAULT_EXPLORE = [
  ["Destinations", "/destinations"],
  ["Recommendations", "/recommendation"],
  ["Photo Gallery", "/gallery"],
  ["Compare Places", "/compare"],
]

const DEFAULT_PLAN = [
  ["Trip Planner", "/itinerary"],
  ["Travel Packages", "/packages"],
  ["Budget Estimator", "/budget-estimator"],
  ["Hotels & Lodges", "/hotels/search"],
]

const Footer = () => {
  const { isAuthenticated } = useAuth()
  const { branding = {}, navigation = [], pageCMS } = usePublicConfig()
  const { showBlock, extras } = pageCMS("footer", ["symbols", "explore", "provinces", "company", "contact", "newsletter"])
  const [email, setEmail] = useState("")
  const [subscribing, setSubscribing] = useState(false)
  const [newsletterMessage, setNewsletterMessage] = useState("")

  const managed = (location) => (navigation || [])
    .filter((item) => item.location === location && String(item.route || "").startsWith("/") && (isAuthenticated || PUBLIC_FOOTER_PATHS.has(item.route)))
    .map((item) => [item.label, item.route])
  const exploreLinks = managed("footer").length ? managed("footer") : DEFAULT_EXPLORE
  // Never publish a placeholder number such as "+977-000-0000" that an old
  // settings row may still hold — show the honest "not published" text.
  const contactPhone = isRealPhone(branding.contact_phone) ? branding.contact_phone : ""
  const contactEmail = /@example\.(com|org)$/i.test(String(branding.contact_email || "")) ? "" : branding.contact_email
  const hasContact = Boolean(branding.contact_address || contactEmail || contactPhone)
  const footerText = branding.footer_text && branding.footer_text.trim() !== APP_NAME ? branding.footer_text : "All rights reserved."

  const subscribe = async (event) => {
    event.preventDefault()
    if (subscribing) return
    setSubscribing(true)
    setNewsletterMessage("")
    try {
      const response = await configApi.subscribeNewsletter(email.trim())
      setNewsletterMessage(response.data?.message || "You are on the list.")
      setEmail("")
    } catch (error) {
      setNewsletterMessage(error.response?.data?.detail || "We could not subscribe you right now.")
    } finally {
      setSubscribing(false)
    }
  }

  return (
    <footer className="mt-16 border-t border-[#B9CEC5] bg-[var(--ny-green-deepest)] text-[#EAF2EF]">
      <div className="border-b border-white/10">
        <div className="container-app grid gap-6 py-10 md:grid-cols-[1fr_auto] md:items-center">
          <div>
            <p className="ny-kicker !border !border-[#63E6BE]/30 !bg-white/10 !text-[#BDEBD9]">Plan with confidence</p>
            <h2 className="mt-3 !text-2xl !text-white sm:!text-3xl">Your Nepal journey starts here.</h2>
            <p className="mt-2 max-w-2xl text-sm text-[#C7D9D2]">Explore recorded places, shape an itinerary, and keep the information you need close while you travel.</p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Link to="/destinations" className="ny-btn ny-btn-accent">Explore Nepal <FiArrowRight size={16} aria-hidden="true" /></Link>
            <Link to="/itinerary" className="ny-btn border border-white/30 bg-transparent text-white hover:border-white hover:bg-white/10">Build my trip</Link>
          </div>
        </div>
      </div>

      {showBlock("symbols") && (
        <section className="container-app border-b border-white/10 py-9" aria-labelledby="footer-symbols-title">
          <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
            <div>
              <h2 id="footer-symbols-title" className="text-lg font-bold text-white">National symbols</h2>
              <p className="mt-1 text-sm text-[#AFC5BC]">A small visual introduction to the identity of Nepal.</p>
            </div>
            <Link to="/discover-nepal" className="inline-flex items-center gap-2 text-sm font-semibold text-[#BDEBD9] hover:text-white">Explore Nepal's story <FiArrowRight size={15} aria-hidden="true" /></Link>
          </div>
          <div className="mt-5 grid grid-cols-4 gap-3 sm:grid-cols-8">
            {NATIONAL_SYMBOLS.map(([title, image]) => (
              <div key={title} className="group text-center">
                <div className="mx-auto grid h-14 w-14 place-items-center overflow-hidden rounded-full border border-[#63E6BE]/30 bg-white/10 transition group-hover:border-[#63E6BE] group-hover:bg-white/15">
                  <img src={image} alt={title} loading="lazy" className="h-full w-full object-cover transition duration-200 group-hover:scale-105" />
                </div>
                <p className="mt-2 text-[11px] leading-4 text-[#C7D9D2]">{title}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      <div className="container-app grid gap-10 py-10 sm:grid-cols-2 lg:grid-cols-3">
        <div className="sm:col-span-2 lg:col-span-1">
          <Link to="/" className="inline-flex items-center gap-2 text-lg font-bold text-white"><FiGlobe size={20} className="text-[#63E6BE]" aria-hidden="true" />{APP_NAME}</Link>
          <p className="mt-3 max-w-sm text-sm leading-6 text-[#AFC5BC]">Discover Nepal beyond Everest — destinations, culture, adventure, wildlife and experiences across the country.</p>
          {showBlock("newsletter") && (
            <form onSubmit={subscribe} className="mt-5 max-w-sm">
              <label htmlFor="footer-newsletter-email" className="text-sm font-semibold text-white">Travel notes, when there is something useful to share</label>
              <div className="mt-2 flex gap-2">
                <input id="footer-newsletter-email" type="email" required value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" className="min-w-0 flex-1 !border-white/20 !bg-white/10 !text-white" />
                <button type="submit" disabled={subscribing} className="ny-btn ny-btn-accent shrink-0">{subscribing ? "Joining…" : "Join"}</button>
              </div>
              {newsletterMessage && <p className="mt-2 text-xs text-[#BDEBD9]" role="status">{newsletterMessage}</p>}
            </form>
          )}
        </div>

        {showBlock("explore") && <FooterColumn title="Explore" links={exploreLinks} />}
        {showBlock("explore") && <FooterColumn title="Plan" links={DEFAULT_PLAN} />}
        {showBlock("company") && <FooterColumn title="Nepal Yatra" links={[["About", "/about"], ["How it works", "/how-it-works"], ["Contact", "/contact"], ["Support", "/support"], ["Emergency", "/emergency"]]} />}
        {showBlock("provinces") && <FooterColumn title="Provinces" links={PROVINCES.map((province) => [province, `/destinations?q=${encodeURIComponent(province)}`])} />}

        {showBlock("contact") && (
          <section aria-labelledby="footer-contact-title">
            <h2 id="footer-contact-title" className="text-sm font-bold text-[#BDEBD9]">Contact</h2>
            {hasContact ? (
              <ul className="mt-4 space-y-3 text-sm text-[#C7D9D2]">
                {branding.contact_address && <li className="flex gap-2"><FiMapPin size={16} className="mt-0.5 shrink-0 text-[#63E6BE]" aria-hidden="true" />{branding.contact_address}</li>}
                {contactEmail && <li className="flex items-center gap-2"><FiMail size={16} className="shrink-0 text-[#63E6BE]" aria-hidden="true" /><a className="break-all hover:text-white" href={`mailto:${contactEmail}`}>{contactEmail}</a></li>}
                {contactPhone && <li className="flex items-center gap-2"><FiPhone size={16} className="shrink-0 text-[#63E6BE]" aria-hidden="true" /><a className="hover:text-white" href={`tel:${String(contactPhone).replace(/[^+\d]/g, "")}`}>{contactPhone}</a></li>}
              </ul>
            ) : <p className="mt-4 text-sm text-[#AFC5BC]">Contact details are not currently published.</p>}
            <div className="mt-5 flex gap-4 text-[#C7D9D2]">
              {branding.facebook_url && <a href={branding.facebook_url} target="_blank" rel="noreferrer" aria-label="Facebook"><FiFacebook size={19} /></a>}
              {branding.instagram_url && <a href={branding.instagram_url} target="_blank" rel="noreferrer" aria-label="Instagram"><FiInstagram size={19} /></a>}
              {branding.twitter_url && <a href={branding.twitter_url} target="_blank" rel="noreferrer" aria-label="X"><FiTwitter size={19} /></a>}
              {branding.youtube_url && <a href={branding.youtube_url} target="_blank" rel="noreferrer" aria-label="YouTube"><FiYoutube size={19} /></a>}
            </div>
          </section>
        )}
      </div>

      {extras?.length > 0 && <div className="container-app border-t border-white/10 py-6 text-sm text-[#C7D9D2]"><CMSExtras sections={extras} /></div>}
      {/* Bottom padding / right gutter keep the floating chat button (fixed
          bottom-right, higher on mobile above the bottom nav) from covering
          the copyright row and the legal links. */}
      <div className="border-t border-white/10 bg-black/20 pt-4 pb-28 sm:pb-5">
        <div className="container-app flex flex-col gap-3 text-xs text-[#C7D9D2] sm:flex-row sm:items-center sm:justify-between sm:pr-20">
          <p>© {new Date().getFullYear()} {APP_NAME}. {footerText}</p>
          <nav aria-label="Legal" className="flex flex-wrap gap-4"><Link to="/privacy" className="hover:text-white">Privacy</Link><Link to="/terms" className="hover:text-white">Terms</Link><Link to="/support" className="hover:text-white">Accessibility & support</Link><Link to="/how-it-works" className="hover:text-white">How it works</Link></nav>
        </div>
      </div>
    </footer>
  )
}

const isRealPhone = (value) => {
  const digits = String(value || "").replace(/\D/g, "")
  if (digits.length < 6) return false
  // Placeholders: long runs of zeros ("+977-000-0000") or one repeated digit.
  return !/0{6,}/.test(digits.replace(/^977/, "")) && !/^(\d)\1+$/.test(digits)
}

const FooterColumn = ({ title, links }) => (
  <section>
    <h2 className="text-sm font-bold text-[#BDEBD9]">{title}</h2>
    <ul className="mt-4 space-y-2.5 text-sm text-[#C7D9D2]">
      {links.map(([label, route]) => <li key={`${label}-${route}`}><Link to={route} className="hover:text-white">{label}</Link></li>)}
    </ul>
  </section>
)

export default Footer
