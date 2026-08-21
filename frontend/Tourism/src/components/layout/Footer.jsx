import { Link } from "react-router-dom";
import {
  FiFacebook,
  FiInstagram,
  FiTwitter,
  FiMapPin,
  FiMail,
  FiPhone,
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
  const { showBlock, copy, extras } = pageCMS("footer", ["symbols", "explore", "provinces", "company", "contact", "tagline"])
  const footerNav = (navigation || []).filter(item => item.location === "footer" && String(item.route || "").startsWith("/"))
  const siteTitle = branding.site_title || APP_NAME
  const footerText = copy("tagline", "body", branding.footer_text || "Discover destinations, plan budgets, and travel safely through Nepal.")
  const contactEmail = branding.contact_email || "support@tourists.app"
  const contactPhone = branding.contact_phone || "+977-000-0000"

  return (

    <footer className="bg-dark text-gray-300 mt-16">

      <div className="h-1 bg-gradient-to-r from-nepalred-500 via-saffron-500 to-forest-500" />


      {showBlock("symbols") && <div className="container-app py-8 border-b border-gray-700">


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
                  border-white/30
                "
              />


              <span className="text-xs mt-2">
                {item.title}
              </span>

            </div>

          ))}

        </div>


        <p className="mt-6 text-right text-sm italic text-saffron-400">
          {copy("symbols", "body", "Discover Nepal — Beyond Everest")}
        </p>
      </div>}




      <div className="container-app py-12 grid grid-cols-1 md:grid-cols-5 gap-8">
        <div>
          <h3 className="text-white text-xl font-bold mb-3">{siteTitle}</h3>
          <p className="text-sm text-gray-400">{footerText}</p>
        </div>

        {showBlock("explore") && (
          <div>
            <h4 className="text-white font-semibold mb-3">{copy("explore", "title", "Explore")}</h4>
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
                <li key={item.route}><Link to={item.route} className="hover:text-white">{item.label}</Link></li>
              ))}
            </ul>
          </div>
        )}

        {showBlock("provinces") && (
          <div>
            <h4 className="text-white font-semibold mb-3">{copy("provinces", "title", "Provinces")}</h4>
            <ul className="space-y-2 text-sm">
              {PROVINCE_CITY_LINKS.map((province) => (
                <li key={province.name}>
                  <Link to={`/destinations?q=${encodeURIComponent(province.city)}`} className="hover:text-white">{province.name}</Link>
                </li>
              ))}
            </ul>
          </div>
        )}

        {showBlock("company") && (
          <div>
            <h4 className="text-white font-semibold mb-3">{copy("company", "title", "Company")}</h4>
            <ul className="space-y-2 text-sm">
              <li><Link to="/about" className="hover:text-white">About Us</Link></li>
              <li><Link to="/contact" className="hover:text-white">Contact</Link></li>
              <li><Link to="/emergency" className="hover:text-white">Emergency</Link></li>
            </ul>
            <div className="mt-4 text-xs space-y-1 text-gray-400">
              <p>🚓 Police:<a href="tel:100" className="text-white ml-1">100</a></p>
              <p>🚑 Ambulance:<a href="tel:102" className="text-white ml-1">102</a></p>
              <p>🔥 Fire:<a href="tel:101" className="text-white ml-1">101</a></p>
            </div>
          </div>
        )}

        {showBlock("contact") && (
          <div>
            <h4 className="text-white font-semibold mb-3">{copy("contact", "title", "Contact")}</h4>
            <ul className="space-y-3 text-sm">
              <li className="flex gap-2 items-center"><FiMapPin /> Pokhara, Nepal</li>
              <li className="flex gap-2 items-center"><FiMail /> {contactEmail}</li>
              <li className="flex gap-2 items-center"><FiPhone /> {contactPhone}</li>
            </ul>
            <div className="flex gap-4 mt-5 text-lg">
              {branding.facebook_url && <a href={branding.facebook_url} target="_blank" rel="noopener noreferrer" className="hover:text-white" aria-label="Facebook"><FiFacebook /></a>}
              {branding.instagram_url && <a href={branding.instagram_url} target="_blank" rel="noopener noreferrer" className="hover:text-white" aria-label="Instagram"><FiInstagram /></a>}
              {branding.twitter_url && <a href={branding.twitter_url} target="_blank" rel="noopener noreferrer" className="hover:text-white" aria-label="X or Twitter"><FiTwitter /></a>}
            </div>
          </div>
        )}
      </div>





      {extras?.length > 0 && <div className="container-app pb-8 text-white"><CMSExtras sections={extras} /></div>}

      <div className="border-t border-gray-700 py-4 text-center text-xs text-gray-500">

        © {new Date().getFullYear()} {siteTitle}. All rights reserved.

      </div>


    </footer>

  );

};


export default Footer;