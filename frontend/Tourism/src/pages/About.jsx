import { motion } from "framer-motion"
import { FiUsers, FiTarget, FiGlobe } from "react-icons/fi"

const VALUES = [
  { icon: FiTarget, title: "Our Mission", desc: "Make local travel planning simple, safe and data-driven for every tourist.", accent: "primary" },
  { icon: FiUsers, title: "Our Community", desc: "Thousands of travelers share reviews, tips and favorite spots every month.", accent: "secondary" },
  { icon: FiGlobe, title: "Our Reach", desc: "Covering destinations across the region with real-time alerts and translations.", accent: "marigold" },
]

const ACCENT_CLASSES = {
  primary: "bg-primary-50 text-primary-500",
  secondary: "bg-secondary-50 text-secondary-500",
  marigold: "bg-marigold-50 text-marigold-500",
}

const About = () => (
  <div
    className="py-16"
    style={{
      background:
        "linear-gradient(180deg, #EAF7F5 0%, #FEF6E7 45%, #FDF1F1 100%)",
    }}
  >
    <div className="container-app">
      <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="section-title text-center">
        About Tourist
      </motion.h1>
      <p className="max-w-2xl mx-auto text-center text-gray-500 mb-12">
        Tourist is a local tourism information portal built to help travelers discover destinations,
        plan budgets, stay safe, and navigate confidently — all from a single platform.
      </p>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {VALUES.map(({ icon: Icon, title, desc, accent }) => (
          <motion.div
            key={title}
            whileHover={{ y: -4 }}
            className="card-base p-6 text-center"
          >
            <div className={`inline-flex p-3 rounded-full mb-4 ${ACCENT_CLASSES[accent]}`}>
              <Icon size={24} />
            </div>
            <h3 className="font-semibold mb-2">{title}</h3>
            <p className="text-sm text-gray-500">{desc}</p>
          </motion.div>
        ))}
      </div>
    </div>
  </div>
)

export default About