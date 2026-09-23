import { FiInbox } from "react-icons/fi"

const EmptyState = ({ title = "Nothing here yet", subtitle = "", icon: Icon = FiInbox, action }) => (
  <div className="flex flex-col items-center justify-center text-center py-16 text-gray-400">
    <div className="p-4 bg-gray-50 rounded-full mb-4">
      <Icon size={48} className="text-gray-300" />
    </div>
    <p className="font-semibold text-gray-600">{title}</p>
    {subtitle && <p className="text-sm mt-1 max-w-md">{subtitle}</p>}
    {action && <div className="mt-4">{action}</div>}
  </div>
)

export default EmptyState
