import { FiInbox } from "react-icons/fi"

const EmptyState = ({ title = "Nothing here yet", subtitle = "", icon: Icon = FiInbox }) => (
  <div className="flex flex-col items-center justify-center text-center py-16 text-gray-400">
    <Icon size={48} className="mb-4" />
    <p className="font-semibold text-gray-600">{title}</p>
    {subtitle && <p className="text-sm mt-1">{subtitle}</p>}
  </div>
)

export default EmptyState