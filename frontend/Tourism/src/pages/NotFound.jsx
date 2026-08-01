import { Link } from "react-router-dom"
import { motion } from "framer-motion"
import { FiCompass } from "react-icons/fi"

const NotFound = () => (
  <div className="min-h-[70vh] flex flex-col items-center justify-center text-center px-4">
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex flex-col items-center"
    >
      <div className="p-4 rounded-full bg-himalaya-50 text-himalaya-500 mb-4">
        <FiCompass size={32} />
      </div>
      <h1 className="text-6xl font-extrabold text-himalaya-500">404</h1>
      <p className="text-gray-500 mt-3 mb-6 max-w-sm">
        Looks like this trail doesn't exist. Let's get you back on route.
      </p>
      <Link to="/" className="btn-primary">Back to Home</Link>
    </motion.div>
  </div>
)

export default NotFound