import "./ChartSetup"
import { Pie } from "react-chartjs-2"

const COLORS = ["#FF5A5F", "#00A699", "#FFB400", "#7B61FF", "#2D9CDB"]

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