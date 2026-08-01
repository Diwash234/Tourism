import "./ChartSetup"
import { Line } from "react-chartjs-2"

const LineChartCard = ({ title, labels, data, label = "Value" }) => {
  const chartData = {
    labels,
    datasets: [
      {
        label,
        data,
        // FIXED: was #FF5A5F (old coral brand color), same raw-hex
        // issue as BarChartCard.jsx.
        borderColor: "#0B3D91",
        backgroundColor: "rgba(11,61,145,0.15)",
        tension: 0.4,
        fill: true,
      },
    ],
  }
  return (
    <div className="card-base p-5">
      {title && <h4 className="font-semibold mb-4">{title}</h4>}
      <Line data={chartData} options={{ responsive: true, plugins: { legend: { display: false } } }} />
    </div>
  )
}

export default LineChartCard