import { Link } from "react-router-dom"
import { FiFacebook, FiInstagram, FiTwitter, FiMapPin, FiMail, FiPhone } from "react-icons/fi"
import { APP_NAME } from "../../utils/constants"

const Footer = () => {
  return (
    <footer className="bg-dark text-gray-300 mt-16">
      <div className="container-app py-12 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div>
          <h3 className="text-white text-xl font-bold mb-3">{APP_NAME}</h3>
          <p className="text-sm text-gray-400">
            Discover local destinations, plan smart budgets, and travel safely with
            real-time alerts and navigation.
          </p>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-3">Explore</h4>
          <ul className="space-y-2 text-sm">
            <li><Link to="/destinations" className="hover:text-white">Destinations</Link></li>
            <li><Link to="/recommendation" className="hover:text-white">Recommendations</Link></li>
            <li><Link to="/budget-estimator" className="hover:text-white">Budget Estimator</Link></li>
            <li><Link to="/risk-alerts" className="hover:text-white">Risk Alerts</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-3">Company</h4>
          <ul className="space-y-2 text-sm">
            <li><Link to="/about" className="hover:text-white">About Us</Link></li>
            <li><Link to="/contact" className="hover:text-white">Contact</Link></li>
            <li><Link to="/emergency" className="hover:text-white">Emergency</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-3">Contact</h4>
          <ul className="space-y-2 text-sm">
            <li className="flex items-center gap-2"><FiMapPin /> Pokhara, Nepal</li>
            <li className="flex items-center gap-2"><FiMail /> support@tourists.app</li>
            <li className="flex items-center gap-2"><FiPhone /> +977-000-0000</li>
          </ul>
          <div className="flex gap-4 mt-4 text-lg">
            <FiFacebook className="hover:text-white cursor-pointer" />
            <FiInstagram className="hover:text-white cursor-pointer" />
            <FiTwitter className="hover:text-white cursor-pointer" />
          </div>
        </div>
      </div>
      <div className="border-t border-gray-700 py-4 text-center text-xs text-gray-500">
        © {new Date().getFullYear()} {APP_NAME}. All rights reserved.
      </div>
    </footer>
  )
}

export default Footer