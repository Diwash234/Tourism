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

  estimate: (data) =>
    axiosClient.post(
      "/ml/budget/",
      data
    ),

  getSummary: () =>
    axiosClient.get("/budget/summary/")

}

export default budgetApi