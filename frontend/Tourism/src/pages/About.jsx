import { motion } from "framer-motion"
import { FiUsers, FiTarget, FiGlobe, FiMessageCircle } from "react-icons/fi"
import { useNavigate } from "react-router-dom"

const About = () => {
  const navigate = useNavigate()

  return (
    <div className="container-app py-16">
      <motion.h1
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="section-title text-center"
      >
        About Tourist
      </motion.h1>

      <p className="max-w-2xl mx-auto text-center text-gray-500 mb-12">
        Tourist is a local tourism information portal built to help travelers
        discover destinations, plan budgets, stay safe, and navigate confidently
        from a single platform.
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
            <div className="inline-flex p-3 rounded-full bg-secondary-500/10 text-secondary-500 mb-4">
              <Icon size={24} />
            </div>

            <h3 className="font-semibold mb-2">{title}</h3>

            <p className="text-sm text-gray-500">{desc}</p>
          </div>
        ))}
      </div>

      {/* Chatbot Feature */}

      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="card-base p-10 text-center bg-gradient-to-r from-primary-500 to-secondary-500 text-white"
      >
        <div className="flex justify-center mb-5">
          <FiMessageCircle size={50} />
        </div>

        <h2 className="text-3xl font-bold mb-4">
          AI Travel Assistant
        </h2>

        <p className="max-w-2xl mx-auto mb-8 text-white/90">
          Chat with our AI assistant powered by OpenAI. Get destination
          recommendations, travel budgets, itinerary planning, emergency
          information, nearby hospitals, police stations, hotels, restaurants,
          and much more.
        </p>

        <button
          onClick={() => navigate("/chatbot")}
          className="bg-white text-primary-600 px-8 py-3 rounded-xl font-semibold hover:scale-105 transition"
        >
          Open Travel Assistant
        </button>
      </motion.div>
    </div>
  )
}

export default About
