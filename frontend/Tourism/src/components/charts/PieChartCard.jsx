import "./ChartSetup"
import { Pie } from "react-chartjs-2"

// FIXED: was ["#FF5A5F", "#00A699", "#FFB400", "#7B61FF", "#2D9CDB"] — a
// generic palette unrelated to the Nepal brand, same raw-hex issue as
// the other two chart components.
const COLORS = ["#0B3D91", "#1B8A5A", "#F59E0B", "#DC143C", "#3f66b8"]

const PieChartCard = ({ title, labels, data }) => {
  const chartData = {
    labels,
    datasets: [{ data, backgroundColor: COLORS }],
  }
  return (
    <div className="card-base p-5">
      {title && <h4 className="font-semibold mb-4">{title}</h4>}
      <Pie data={chartData} options={{ responsive: true }} />
    </div>
  )
}

export default PieChartCard