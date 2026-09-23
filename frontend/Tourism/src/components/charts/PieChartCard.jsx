import ChartCard from "./ChartCard"

const PieChartCard = ({ title, labels, data }) => (
  <ChartCard type="pie" title={title} labels={labels} data={data} />
)

export default PieChartCard
