import { Link } from "react-router-dom"
import { FiArrowRight, FiCompass, FiGlobe, FiHeart, FiShield, FiUsers } from "react-icons/fi"
import { APP_NAME } from "../utils/constants"
import usePublicConfig from "../hooks/usePublicConfig"
import CMSIntro from "../components/cms/CMSIntro"
import PageHeader from "../components/common/PageHeader"

const VALUES = [
  [FiCompass, "Useful before you book", "We organise the information a traveller needs to make a confident first decision."],
  [FiShield, "Clear about uncertainty", "When a record is missing, we say so rather than filling the gap with a guess."],
  [FiHeart, "Rooted in Nepal", "The product is shaped around the country's landscapes, communities, languages and travel realities."],
  [FiUsers, "Open to local knowledge", "Travellers and local contributors can help keep the catalogue useful, with review before publication."],
]

export default function About() {
  const { block } = usePublicConfig().pageCMS("about", ["intro", "page-intro"])
  return <div className="ny-page container-app section-space"><CMSIntro section={block("intro")} /><PageHeader title={`About ${APP_NAME}`} subtitle="A practical travel information platform for discovering Nepal, planning with context and finding support when you need it." icon={FiGlobe} /><div className="ny-reading text-center"><p className="text-base leading-7 text-[var(--ny-text-secondary)]">Nepal Yatra brings destinations, routes, budgets, stays and safety information into one calm journey — without pretending that every answer is available.</p></div><div className="mt-10 grid gap-5 sm:grid-cols-2 lg:grid-cols-4">{VALUES.map(([Icon, title, description]) => <article key={title} className="ny-card flex h-full flex-col p-5"><span className="grid h-11 w-11 place-items-center rounded-[var(--ny-radius-md)] bg-[var(--ny-soft-green)] text-[var(--ny-green)]"><Icon size={20} aria-hidden="true" /></span><h2 className="mt-5 text-lg font-bold">{title}</h2><p className="mt-2 text-sm leading-6 text-[var(--ny-text-secondary)]">{description}</p></article>)}</div><section className="mt-12 rounded-[var(--ny-radius-xl)] bg-[var(--ny-green-dark)] p-7 text-white sm:p-10"><div className="flex flex-col gap-6 md:flex-row md:items-center md:justify-between"><div><p className="text-sm font-semibold text-[#BDEBD9]">Start with a place</p><h2 className="mt-2 !text-2xl !text-white">See what Nepal Yatra can help you find.</h2><p className="mt-2 max-w-2xl text-sm leading-6 text-[#C7D9D2]">Explore the catalogue, compare destinations and build a trip around the way you actually want to travel.</p></div><Link to="/destinations" className="ny-btn ny-btn-accent shrink-0">Explore destinations <FiArrowRight size={16} aria-hidden="true" /></Link></div></section></div>
}
