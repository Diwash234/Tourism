import { FiHelpCircle } from "react-icons/fi"

/**
 * Safe icon wrapper. React rendering errors belong to an Error Boundary;
 * try/catch around JSX cannot catch them and also violates the React compiler
 * error-boundary rule.
 */
export const SafeIcon = ({ icon: Icon, fallback = FiHelpCircle, ...props }) => {
  const IconComponent = Icon || fallback || FiHelpCircle
  return <IconComponent {...props} />
}

export const getIcon = (key, iconMap, fallback = FiHelpCircle) => {
  return iconMap[key] || fallback
}

export default SafeIcon
