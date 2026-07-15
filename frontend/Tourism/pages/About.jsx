import { motion } from "framer-motion"
import { FiUsers, FiTarget, FiGlobe } from "react-icons/fi"

const About = () => (
  <div className="container-app py-16">
    <motion.h1 initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="section-title text-center">
      About Tourist
    </motion.h1>
    <p className="max-w-2xl mx-auto text-center text-gray-500 mb-12">
      Tourist is a local tourism information portal built to help travelers discover destinations,
      plan budgets, stay safe, and navigate confidently — all from a single platform.
    </p>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {[
        { icon: FiTarget, title: "Our Mission", desc: "Make local travel planning simple, safe and data-driven for every tourist." },
        { icon: FiUsers, title: "Our Community", desc: "Thousands of travelers share reviews, tips and favorite spots every month." },
        { icon: FiGlobe, title: "Our Reach", desc: "Covering destinations across the region with real-time alerts and translations." },
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
  </div>
)

export default About