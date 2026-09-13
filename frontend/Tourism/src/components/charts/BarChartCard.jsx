import ChartCard from "./ChartCard"

const BarChartCard = ({ title, labels, data, label = "Value" }) => (
  <ChartCard type="bar" title={title} labels={labels} data={data} label={label} />
)

export default BarChartCard
