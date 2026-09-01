import "./ChartSetup"
import { Bar } from "react-chartjs-2"

const BarChartCard = ({ title, labels, data, label = "Value" }) => {
  const chartData = {
    labels,
    datasets: [
      {
        label,
        data,
        // string in Chart.js config, invisible to the Tailwind color
        // retheme done earlier this session since that only affects
        // generated CSS classes, not JS literals.
        backgroundColor: "#1B8A5A",
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