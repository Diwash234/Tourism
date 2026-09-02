import { Link } from "react-router-dom";
import {
  FiFacebook,
  FiInstagram,
  FiTwitter,
  FiMapPin,
  FiMail,
  FiPhone,
  FiBookOpen,
} from "react-icons/fi";

import { APP_NAME } from "../../utils/constants";
import usePublicConfig from "../../hooks/usePublicConfig";
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
  const { showBlock, copy, extras } = pageCMS("footer", ["symbols", "explore", "provinces", "company", "contact"])
  const footerNav = (navigation || []).filter(item => item.location === "footer" && String(item.route || "").startsWith("/"))
  
  const rawTitle = branding.site_title || APP_NAME
  const siteTitle = rawTitle.replace(/Digital Nepal Tourism Platform/g, "Nepal Yatra").replace(/Digital Nepal Tourism/g, "Nepal Yatra").replace(/Digital Nepal/g, "Nepal Yatra")
  
  const contactAddress = branding.contact_address || "Pokhara, Nepal"
  const contactEmail = branding.contact_email || "support@tourists.app"
  const contactPhone = branding.contact_phone || "+977-000-0000"

  return (
    <footer className="bg-slate-950 text-emerald-100 mt-16 border-t border-emerald-500/30">
      <div className="h-1 bg-gradient-to-r from-emerald-500 via-teal-400 to-emerald-400" />

      {showBlock("symbols") && <div className="container-app py-8 border-b border-emerald-900/60">
        <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-8 gap-5">
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
            className="px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-300 text-slate-950 font-black text-xs shadow flex items-center gap-2 transition-transform hover:scale-105"
          >
            <FiBookOpen size={16} /> See More — Explore All 26 National Symbols & Country Profile ➔
          </Link>

          <p className="text-sm italic text-emerald-400 font-semibold">
            {copy("symbols", "body", "Discover Nepal — Beyond Everest")}
          </p>
        </div>
      </div>}

      <div className="container-app py-12 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-8">
        {showBlock("explore") && (
          <div>
            <h4 className="text-emerald-400 font-bold mb-3 text-sm uppercase tracking-wider">{copy("explore", "title", "Explore")}</h4>
            <ul className="space-y-2 text-sm">
              {(footerNav.length
                ? footerNav.filter((item) => ["/destinations", "/recommendation", "/budget-estimator", "/risk-alerts"].includes(item.route))
                : [
                    { label: "Destinations", route: "/destinations" },
                    { label: "Recommendations", route: "/recommendation" },
                    { label: "Budget Estimator", route: "/budget-estimator" },
                    { label: "Risk Alerts", route: "/risk-alerts" },
                  ]
              ).map((item) => (
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
              <li><Link to="/how-it-works" className="text-emerald-300 font-bold hover:text-white">How It Works</Link></li>
              <li><Link to="/support" className="text-emerald-300 font-bold hover:text-white">Customer Support</Link></li>
              <li><Link to="/about" className="text-emerald-200 hover:text-white transition-colors">About Us</Link></li>
              <li><Link to="/contact" className="text-emerald-200 hover:text-white transition-colors">Contact</Link></li>
              <li><Link to="/privacy" className="text-emerald-200 hover:text-white transition-colors">Privacy Policy</Link></li>
              <li><Link to="/terms" className="text-emerald-200 hover:text-white transition-colors">Terms of Service</Link></li>
              <li><Link to="/emergency" className="text-emerald-200 hover:text-white transition-colors">Emergency</Link></li>
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
            </div>
          </div>
        )}
      </div>

      {extras?.length > 0 && <div className="container-app pb-8 text-emerald-100"><CMSExtras sections={extras} /></div>}

      <div className="border-t border-emerald-900/60 py-4 text-center text-xs text-emerald-300">
        © {new Date().getFullYear()} {siteTitle}. All rights reserved.
        <button type="button" onClick={() => window.scrollTo({ top: 0, behavior: "smooth" })} className="ml-4 font-bold text-emerald-400 hover:text-white hover:underline">Back to top</button>
      </div>
    </footer>
  );
};

export default Footer;