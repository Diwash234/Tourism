import { renderToStaticMarkup } from "react-dom/server"
import ChartCard, { signatureFor, hasChartData, makeChartData, makeChartOptions } from "../src/components/charts/ChartCard.jsx"
import BarChartCard from "../src/components/charts/BarChartCard.jsx"

let fails = 0
const check = (name, cond, extra = "") => {
  console.log(`${cond ? "PASS" : "FAIL"}  ${name}${extra ? " :: " + extra : ""}`)
  if (!cond) fails++
}

// 1. The core fix: identical content, different array identity -> same signature.
const a = signatureFor("bar", ["Low", "High"], [1, 2], "Value")
const b = signatureFor("bar", ["Low", "High"], [1, 2], "Value")
check("signature ignores array identity", a === b, a)
check("signature changes with content", a !== signatureFor("bar", ["Low", "High"], [1, 3], "Value"))
check("signature changes with type", a !== signatureFor("pie", ["Low", "High"], [1, 2], "Value"))

// 2. Empty-data guard.
check("hasChartData false when empty", hasChartData([], []) === false)
check("hasChartData false when undefined", hasChartData(undefined, undefined) === false)
check("hasChartData true with data", hasChartData(["Low"], [3]) === true)

// 3. Config shapes.
const bar = makeChartData("bar", ["A"], [1], "V", ["#1B8A5A"])
check("bar config", bar.datasets[0].backgroundColor === "#1B8A5A" && bar.datasets[0].borderRadius === 6, JSON.stringify(bar.datasets[0]))
const line = makeChartData("line", ["A"], [1], "V", ["#1B8A5A"])
check("line config", line.datasets[0].fill === true && line.datasets[0].tension === 0.4, JSON.stringify(line.datasets[0]))
const pie = makeChartData("pie", ["A"], [1], "V", ["#1B8A5A", "#0B3D91"])
check("pie config uses palette", Array.isArray(pie.datasets[0].backgroundColor) && pie.datasets[0].backgroundColor.length === 2)
check("pie legend shown", makeChartOptions("pie", false).plugins.legend.display === true)
check("bar legend hidden by default", makeChartOptions("bar", false).plugins.legend.display === false)

// 4. Real render through the public wrapper: empty data must render the placeholder,
//    not touch chart.js at all.
const html = renderToStaticMarkup(<BarChartCard title="Risk mix" />)
check("renders title", html.includes("Risk mix"))
check("renders empty-state placeholder", html.includes("No data to chart yet"))
const html2 = renderToStaticMarkup(<ChartCard type="line" />)
check("placeholder for undefined data too", html2.includes("No data to chart yet"))

console.log(fails === 0 ? "\nALL CHECKS PASSED" : `\n${fails} CHECK(S) FAILED`)
process.exit(fails === 0 ? 0 : 1)
