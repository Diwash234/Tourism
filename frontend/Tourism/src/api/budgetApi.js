import axiosClient from "./axiosClient"

// CORRECTED — the previous comment here claimed the backend response was
// flattened to {total, accommodation, food, transport, activities}. I
// traced the actual chain (tourist/views_ml.py -> tourist/utils.py ->
// ml_service/api/budget.py -> model/budget/budget_engine.py) and that's
// not what happens:
//   - estimate_budget() returns `total_budget_usd` and `daily_cost_usd`,
//     NOT `estimated_total`. views_ml.py does
//     `flattened["total"] = result.get("estimated_total")`, which is
//     always None, since that key doesn't exist in the ML response.
//   - The breakdown keys are `transport`, `food`, `accommodation`,
//     `local_transport` — there is no `activities` key anywhere.
//   - Bigger issue: ml_service's BudgetRequest (api/budget.py) only
//     declares `transport_cost`, `food_cost_day`, `accommodation_night`,
//     `taxi_cost`, `days` — it silently ignores `travelers`,
//     `budget_level`, `city`, and `country`, all of which Django sends.
//     So today, changing travelers/style/destination in the form has NO
//     effect on the numbers — only `days` does. See chat notes for the
//     backend fix.
// BudgetEstimator.jsx below reads the REAL field names so the number at
// least displays correctly while that deeper fix is pending.
const budgetApi = {
  estimate: async (data) => {
    try {
      return await axiosClient.post("/ml/budget/", data)
    } catch (err) {
      if (err.response?.status === 503 || err.response?.status === 500) {
        const days = Number(data.days || 3)
        const travelers = Number(data.travelers || 1)
        const level = data.budget_level || data.style || "mid"
        const multiplier = level === "budget" ? 0.75 : level === "luxury" ? 1.8 : 1.0

        const food = Math.round(12 * days * travelers * multiplier)
        const accommodation = Math.round(20 * days * Math.max(1, Math.round(travelers / 2)) * multiplier)
        const transport = Math.round(15 * travelers * multiplier)
        const activities = Math.round(10 * days * travelers)
        const total = food + accommodation + transport + activities

        return {
          data: {
            total_budget_usd: total,
            estimated_total: total,
            total: total,
            daily_cost_usd: Math.round(total / days),
            city: data.city || data.destination || "Nepal",
            travelers: travelers,
            days: days,
            breakdown: {
              food,
              accommodation,
              transport,
              activities,
              local_taxi: Math.round(5 * days * travelers),
            },
            source: "client_fallback",
          },
        }
      }
      throw err
    }
  },

  getSummary: () =>
    axiosClient.get("/budget/summary/")
}

export default budgetApi