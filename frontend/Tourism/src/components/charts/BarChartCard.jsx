import "./ChartSetup"
import { Bar } from "react-chartjs-2"

const BarChartCard = ({ title, labels, data, label = "Value" }) => {
  const chartData = {
    labels,
    datasets: [
      {
        label,
        data,
        backgroundColor: "#00A699",
        borderRadius: 6,
      },
    ],
  }
  return (
    <div className="card-base p-5">
      {title && <h4 className="font-semibold mb-4">{title}</h4>}
      <Bar data={chartData} options={{ responsive: true, plugins: { legend: { display: false } } }} />
    </div>
  )
}

export default BarChartCard