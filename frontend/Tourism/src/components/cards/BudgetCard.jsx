import { FiDollarSign } from "react-icons/fi"
import { formatCurrency } from "../../utils/helpers"

// Tailwind's JIT scanner can only see class names that appear literally in
// source — `bg-${accent}-50` was invisible to it and silently never
// generated (secondary/forest/saffron/himalaya cards rendered with no
// background at all). A static map keeps every class name visible.
const ACCENTS = {
  primary: "bg-primary-50 text-primary-500",
  secondary: "bg-secondary-500/10 text-secondary-600",
  himalaya: "bg-himalaya-50 text-himalaya-500",
  forest: "bg-forest-50 text-forest-500",
  saffron: "bg-saffron-50 text-saffron-600",
  nepalred: "bg-nepalred-50 text-nepalred-500",
}

const BudgetCard = ({ label, amount, icon: Icon = FiDollarSign, accent = "primary" }) => (
  <div className="card-base p-5 flex items-center gap-4">
    <div className={`p-3 rounded-xl ${ACCENTS[accent] || ACCENTS.primary}`}>
      <Icon size={22} />
    </div>
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-xl font-bold text-dark">{formatCurrency(amount)}</p>
    </div>
  </div>
)

export default BudgetCard