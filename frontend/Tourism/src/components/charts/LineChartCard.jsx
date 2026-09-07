import ChartCard from "./ChartCard"

const LineChartCard = ({ title, labels, data, label = "Value" }) => (
  <ChartCard type="line" title={title} labels={labels} data={data} label={label} />
)

export default LineChartCard
