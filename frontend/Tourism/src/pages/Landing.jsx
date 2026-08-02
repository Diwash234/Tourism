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
  {
    icon: FiMapPin,
    title: "Discover Destinations",
    desc: "Explore curated local tourist spots with photos, videos and reviews."
  },
  {
    icon: FiDollarSign,
    title: "Smart Budget Estimator",
    desc: "Plan your trip costs accurately before you travel."
  },
  {
    icon: FiShield,
    title: "Real-time Risk Alerts",
    desc: "Stay informed with safety alerts for every destination."
  },
  {
    icon: FiNavigation,
    title: "Live Navigation",
    desc: "Get routes, nearby hospitals, police stations and attractions."
  },
]


const FAQ_ITEMS = [
  {
    question: "Why should you use our tourism recommendation system instead of searching manually?",
    answer:
      "Manual searching means checking many different websites. Our system combines destination data, ratings, weather, safety information and budget estimates in one place so travelers can make decisions faster."
  },
  {
    question: "How does our website help you discover Nepal destinations?",
    answer:
      "Destinations can be explored by category, season, budget and interests. Each place provides useful information for better travel planning."
  },
  {
    question: "What personalized recommendations can our system provide?",
    answer:
      "The recommendation engine learns from viewed, searched and favorited destinations to suggest places matching traveler interests."
  },
  {
    question: "How does our website save travel planning time?",
    answer:
      "Budget planning, hotels, safety alerts, navigation and destination information are available together instead of using multiple applications."
  },
  {
    question: "How does the recommendation system match destinations?",
    answer:
      "It compares categories, locations, budgets and user activity to provide more relevant destination suggestions."
  },
  {
    question: "Why is this useful for first-time Nepal visitors?",
    answer:
      "The system helps travelers understand safety, costs, weather and attractions before arriving."
  },
  {
    question: "How does the budget system help travelers?",
    answer:
      "It estimates expenses based on travel duration, travelers count and travel style."
  },
  {
    question: "How does it help create itineraries?",
    answer:
      "The system combines distance, season and safety information to help organize better trips."
  },
  {
    question: "Why is it better than random online searches?",
    answer:
      "The platform uses structured destination records instead of depending only on random search results."
  },
  {
    question: "How does it improve travel experience?",
    answer:
      "It reduces uncertainty by providing information about expenses, destinations, safety and recommendations."
  },
]


const Landing = () => {

  const [destinations, setDestinations] = useState([])
  const [loading, setLoading] = useState(true)


  useEffect(() => {

    destinationApi
      .getAll({
        limit: 6,
        featured: true,
      })

      .then(({ data }) => {

        console.log("Destination API:", data)

        setDestinations(
          data.results || data || []
        )

      })

      .catch((error) => {

        console.log(
          "Destination error:",
          error
        )

        setDestinations([])

      })

      .finally(() => {

        setLoading(false)

      })

  }, [])



  return (

    <div className="theme-crimson">


      <section className="relative bg-gradient-to-br from-nepalred-600 via-nepalred-500 to-himalaya-800 text-white overflow-hidden">

        <HeroEffects />


        <div className="container-app py-24 md:py-32 relative z-10">


          <motion.h1

            initial={{
              opacity:0,
              y:20
            }}

            animate={{
              opacity:1,
              y:0
            }}

            className="text-4xl md:text-6xl font-extrabold max-w-2xl leading-tight"

          >

            Explore Local Wonders, Travel Smart & Safe

          </motion.h1>



          <p className="mt-4 text-lg text-white/90 max-w-xl">

            Your all-in-one tourism companion — destinations, budgets, safety alerts, and navigation in one place.

          </p>



          <div className="mt-8 bg-white rounded-xl2 p-2 max-w-xl shadow-hover">

            <SearchBar
              placeholder="Search destinations, cities, attractions..."
              className="w-full"
            />

          </div>



          <div className="mt-6 flex gap-3">


            <Link
              to="/destinations"
              className="bg-white text-primary-600 font-semibold px-6 py-3 rounded-xl hover:bg-gray-100"
            >

              Browse Destinations

            </Link>



            <Link
              to="/register"
              className="border border-white/70 font-semibold px-6 py-3 rounded-xl hover:bg-white/10"
            >

              Get Started

            </Link>


          </div>


        </div>


      </section>



      <NepalHighlights />



      <section className="container-app py-16">

        <h2 className="section-title text-center">

          Why Travel With Us

        </h2>


        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">


          {features.map(({icon:Icon,title,desc}) => (

            <motion.div

              key={title}

              whileHover={{
                y:-4
              }}

              className="card-base p-6 text-center"

            >

              <div className="inline-flex p-3 rounded-full bg-primary-50 text-primary-500 mb-4">

                <Icon size={24}/>

              </div>


              <h3 className="font-semibold mb-2">
                {title}
              </h3>


              <p className="text-sm text-gray-500">
                {desc}
              </p>


            </motion.div>

          ))}


        </div>


      </section>




      <section className="container-app py-16">


        <div className="flex items-center justify-between mb-6">


          <h2 className="section-title mb-0">
            Popular Destinations
          </h2>


          <Link
            to="/destinations"
            className="text-primary-500 font-semibold text-sm hover:underline"
          >

            View all

          </Link>


        </div>




        {loading ? (

          <Loader />

        ) : destinations.length ? (


          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">


            {destinations.map((d)=>(

              <DestinationCard
                key={d.id}
                destination={d}
              />

            ))}


          </div>


        ) : (

          <p className="text-gray-400 text-center py-10">

            Destinations will appear here once the backend is connected.

          </p>

        )}


      </section>




      <section className="container-app py-16">


        <h2 className="section-title text-center mx-auto w-fit">

          Frequently Asked Questions

        </h2>



        <p className="text-gray-500 text-center max-w-2xl mx-auto mb-10 -mt-2">

          Everything travelers usually ask before trusting a recommendation engine over their own search.

        </p>



        <div className="max-w-3xl mx-auto">

          <FAQAccordion items={FAQ_ITEMS}/>

        </div>


      </section>



    </div>

  )

}


export default Landing