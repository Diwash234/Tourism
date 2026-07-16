import { motion } from "framer-motion"
import { FiCheckCircle, FiXCircle, FiInfo, FiAlertTriangle } from "react-icons/fi"

const icons = {
  success: <FiCheckCircle className="text-green-500" size={20} />,
  error: <FiXCircle className="text-red-500" size={20} />,
  warning: <FiAlertTriangle className="text-yellow-500" size={20} />,
  info: <FiInfo className="text-blue-500" size={20} />,
}

const Toast = ({ message, type = "info" }) => (
  <motion.div
    initial={{ opacity: 0, x: 50 }}
    animate={{ opacity: 1, x: 0 }}
    exit={{ opacity: 0, x: 50 }}
    className="flex items-center gap-3 bg-white shadow-hover rounded-xl px-4 py-3 min-w-[260px] border border-gray-100"
  >
    {icons[type]}
    <span className="text-sm text-dark">{message}</span>
  </motion.div>
)

export default Toast