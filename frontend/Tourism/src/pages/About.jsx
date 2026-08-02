import { motion } from "framer-motion"
import { Link } from "react-router-dom"
import { FiUsers, FiTarget, FiGlobe, FiArrowRight } from "react-icons/fi"
import { APP_NAME } from "../utils/constants"

const About = () => (
  <div className="container-app py-16 fade-in theme-maroon">
    <motion.h1
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="section-title text-center mx-auto w-fit"
    >
      About {APP_NAME}
    </motion.h1>

    <p className="max-w-2xl mx-auto text-center text-gray-500 mb-12">
      {APP_NAME} is a local tourism information portal built to help travelers
      discover Nepal's destinations, plan budgets, stay safe, and navigate
      confidently — all from a single platform.
    </p>

    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
      {[
        {
          icon: FiTarget,
          title: "Our Mission",
          desc: "Make local travel planning simple, safe and data-driven for every tourist.",
        },
        {
          icon: FiUsers,
          title: "Our Community",
          desc: "Thousands of travelers share reviews, tips and favorite spots every month.",
        },
        {
          icon: FiGlobe,
          title: "Our Reach",
          desc: "Covering destinations across Nepal with real-time alerts and translations.",
        },
      ].map(({ icon: Icon, title, desc }) => (
        <div key={title} className="card-base p-6 text-center">
          <div className="inline-flex p-3 rounded-full bg-forest-50 text-forest-500 mb-4">
            <Icon size={24} />
          </div>

          <h3 className="font-semibold mb-2">
            {title}
          </h3>

          <p className="text-sm text-gray-500">
            {desc}
          </p>
        </div>
      ))}
    </div>


    <div className="card-base p-8 text-center bg-gradient-to-br from-himalaya-500 to-forest-600 text-white">

      <h2 className="text-xl font-heading font-bold mb-2">
        Ready to explore?
      </h2>

      <p className="text-white/80 mb-5 max-w-md mx-auto">
        See Nepal's history, culture, festivals, and heritage in one place.
      </p>


      <Link
        to="/discover-nepal"
        className="inline-flex items-center gap-2 bg-white text-himalaya-600 font-semibold px-5 py-2.5 rounded-xl hover:-translate-y-0.5 transition-transform"
      >
        Discover Nepal
        <FiArrowRight size={16} />
      </Link>

    </div>

  </div>
)

export default About