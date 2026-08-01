// CONFIRMED WORKING as-is — no changes needed. destinationApi.getAll({limit:6,
// featured:true}) now matches the backend's `limit`->page_size and `featured`
// filter aliases added earlier.
import { useState, useEffect } from "react"
import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import { FiMapPin, FiShield, FiDollarSign, FiNavigation } from "react-icons/fi"
import SearchBar from "../components/common/SearchBar"
import DestinationCard from "../components/cards/DestinationCard"
import Loader from "../components/common/Loader"
import FAQAccordion from "../components/common/FAQAccordion"
import NepalHighlights from "../components/dashboard/NepalHighlights"
import HeroEffects from "../components/dashboard/HeroEffects"
import destinationApi from "../api/destinationApi"

const features = [
  { icon: FiMapPin, title: "Discover Destinations", desc: "Explore curated local tourist spots with photos, videos and reviews." },
  { icon: FiDollarSign, title: "Smart Budget Estimator", desc: "Plan your trip costs accurately before you travel." },
  { icon: FiShield, title: "Real-time Risk Alerts", desc: "Stay informed with safety alerts for every destination." },
  { icon: FiNavigation, title: "Live Navigation", desc: "Get routes, nearby hospitals, police stations and attractions." },
]

const FAQ_ITEMS = [
  {
    question: "Why should you use our tourism recommendation system instead of searching manually?",
    answer:
      "Manual searching means sifting through dozens of generic blog posts and outdated listings. Our system pulls from verified, up-to-date destination data — ratings, current weather, safety status, and budget estimates — and ranks results based on what you've actually shown interest in, so you get relevant answers in seconds instead of hours of tab-hopping.",
  },
  {
    question: "How does our website help you discover the best places to visit in Nepal?",
    answer:
      "Every destination is filterable by category (mountains, culture, adventure, heritage), season, and budget, and each listing includes real ratings, photos from other travelers, and live weather — so you're comparing places on the details that actually matter for planning, not just a name and a photo.",
  },
  {
    question: "What personalized recommendations can our system provide?",
    answer:
      "Once you've viewed, favorited, or searched a few destinations, the recommendation engine surfaces similar places — for example, if you liked a mountain museum, it'll suggest other cultural and heritage sites you're likely to enjoy, rather than showing everyone the same fixed \"top 10\" list.",
  },
  {
    question: "How does our website save you time when planning a trip?",
    answer:
      "Budget estimation, safety information, hotel options, and route planning all live in one dashboard instead of five different tabs — you're not cross-referencing a travel blog, a weather app, a currency converter, and a maps app separately.",
  },
  {
    question: "How does our recommendation system match destinations to your interests?",
    answer:
      "It looks at the categories and destinations you've searched, viewed, or favorited and finds other places with similar characteristics — same category, comparable price range, or nearby location — so recommendations get more relevant to you specifically the more you use the site.",
  },
  {
    question: "Why is our website helpful for first-time visitors to Nepal?",
    answer:
      "First-time visitors don't know which areas are safe, what a fair price looks like, or which sites are worth the trek. Our risk alerts, budget estimator, and curated ratings give you that local context upfront, instead of learning it the hard way after arriving.",
  },
  {
    question: "How does our system recommend attractions based on your budget?",
    answer:
      "The budget planner takes your trip length, number of travelers, and travel style (budget/medium/luxury) and estimates hotel, food, transport, and activity costs — so you can filter destinations and experiences that actually fit what you're willing to spend, before you commit to anything.",
  },
  {
    question: "How does our website help you create a better travel itinerary?",
    answer:
      "By combining destination data, distances, recommended seasons, and safety status in one place, you can sequence a trip logically — grouping nearby destinations, avoiding places flagged with active risk alerts, and timing visits to match the recommended season for each spot.",
  },
  {
    question: "What makes our tourism recommendation system more reliable than random online searches?",
    answer:
      "Generic search results are optimized for ad clicks and SEO, not accuracy — listings go stale, ratings can be manipulated, and safety information is often missing entirely. Our data is structured, moderated, and tied to real destination records with live weather and alert data, not just whichever page ranks highest.",
  },
  {
    question: "How does our website improve your overall travel experience in Nepal?",
    answer:
      "By reducing the guesswork — you know roughly what you'll spend, what the safety situation looks like, what the weather will be, and what similar travelers thought of a place — so you can spend less time researching and more time actually enjoying the trip.",
  },
]

const Landing = () => {
  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(()=>{

 destinationApi
 .getAll({
    limit:6,
    featured:true
 })
 .then(({data})=>{


    console.log("Destination API:",data);


    setDestinations(
       data.results || []
    );


 })
 .catch((error)=>{

    console.log(
      "Destination error",
      error
    );

    setDestinations([]);

 })
 .finally(()=>setLoading(false));


},[]);


  return (
    <div>
      <section className="relative bg-gradient-to-br from-primary-500 to-secondary-500 text-white overflow-hidden">
        <HeroEffects />
        <div className="container-app py-24 md:py-32 relative z-10">
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="text-4xl md:text-6xl font-extrabold max-w-2xl leading-tight"
          >
            Explore Local Wonders, Travel Smart & Safe
          </motion.h1>
          <p className="mt-4 text-lg text-white/90 max-w-xl">
            Your all-in-one tourism companion — destinations, budgets, safety alerts, and navigation in one place.
          </p>
          <div className="mt-8 bg-white rounded-xl2 p-2 max-w-xl shadow-hover">
            <SearchBar placeholder="Search destinations, cities, attractions..." className="w-full" />
          </div>
          <div className="mt-6 flex gap-3">
            <Link to="/destinations" className="bg-white text-primary-600 font-semibold px-6 py-3 rounded-xl hover:bg-gray-100">
              Browse Destinations
            </Link>
            <Link to="/register" className="border border-white/70 font-semibold px-6 py-3 rounded-xl hover:bg-white/10">
              Get Started
            </Link>
          </div>
        </div>
      </section>

      <NepalHighlights />

      <section className="container-app py-16">
        <h2 className="section-title text-center">Why Travel With Us</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {features.map(({ icon: Icon, title, desc }) => (
            <motion.div
              key={title}
              whileHover={{ y: -4 }}
              className="card-base p-6 text-center"
            >
              <div className="inline-flex p-3 rounded-full bg-primary-50 text-primary-500 mb-4">
                <Icon size={24} />
              </div>
              <h3 className="font-semibold mb-2">{title}</h3>
              <p className="text-sm text-gray-500">{desc}</p>
            </motion.div>
          ))}
        </div>
      </section>

      <section className="container-app py-16">
        <div className="flex items-center justify-between mb-6">
          <h2 className="section-title mb-0">Popular Destinations</h2>
          <Link to="/destinations" className="text-primary-500 font-semibold text-sm hover:underline">
            View all
          </Link>
        </div>
        {loading ? (
          <Loader />
        ) : destinations.length ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {destinations.map((d) => (
              <DestinationCard key={d.id} destination={d} />
            ))}
          </div>
        ) : (
          <p className="text-gray-400 text-center py-10">Destinations will appear here once the backend is connected.</p>
        )}
      </section>
      {/* NEW: FAQ accordion — click the chevron to reveal/collapse the answer */}
      <section className="container-app py-16">
        <h2 className="section-title text-center mx-auto w-fit">Frequently Asked Questions</h2>
        <p className="text-gray-500 text-center max-w-2xl mx-auto mb-10 -mt-2">
          Everything travelers usually ask before trusting a recommendation engine over their own search.
        </p>
        <div className="max-w-3xl mx-auto">
          <FAQAccordion items={FAQ_ITEMS} />
        </div>
      </section>
    </div>
  )
}

export default Landing