import { FiDollarSign } from "react-icons/fi"
import { formatCurrency } from "../../utils/helpers"

const BudgetCard = ({ label, amount, icon: Icon = FiDollarSign, accent = "primary" }) => (
  <div className="card-base p-5 flex items-center gap-4">
    <div className={`p-3 rounded-xl bg-${accent}-50 text-${accent}-500`}>
      <Icon size={22} />
    </div>
    <div>
      <p className="text-sm text-gray-500">{label}</p>
      <p className="text-xl font-bold text-dark">{formatCurrency(amount)}</p>
    </div>
  </div>
)

export default BudgetCard