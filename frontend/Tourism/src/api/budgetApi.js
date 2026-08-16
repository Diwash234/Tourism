import axiosClient from "./axiosClient"

const getDestinationDailyTier = (destName = "") => {
  const clean = String(destName).replace(/[^a-zA-Z]/g, "").toLowerCase()
  if (!clean) return { label: "Nepal General Baseline", baseDaily: 35 }
  if (clean.includes("everest") || clean.includes("basecamp") || clean.includes("mustang") || clean.includes("dolpo") || clean.includes("manaslu") || clean.includes("trek")) {
    return { label: "High Alpine Trekking Tier", baseDaily: 55 }
  }
  if (clean.includes("chitwan") || clean.includes("bardiya") || clean.includes("safari") || clean.includes("wildlife")) {
    return { label: "National Park & Safari Tier", baseDaily: 45 }
  }
  if (clean.includes("pokhara") || clean.includes("lakeside") || clean.includes("sarangkot") || clean.includes("annapurna")) {
    return { label: "Lakes & Mid-Hills Tier", baseDaily: 38 }
  }
  return { label: "Cultural & City Tier", baseDaily: 32 }
}

const budgetApi = {
  estimate: async (data) => {
    try {
      return await axiosClient.post("/ml/budget/", data)
    } catch (err) {
      const days = Math.max(1, Number(data.days) || 3)
      const travelers = Math.max(1, Number(data.travelers) || 1)
      const level = data.budget_level || data.style || "mid"
      const multiplier = level === "budget" ? 0.75 : level === "luxury" ? 1.8 : 1.0

      const destInput = data.city || data.destination || "Nepal"
      const { label: tierLabel, baseDaily } = getDestinationDailyTier(destInput)

      const food = Math.round(baseDaily * 0.3 * days * travelers * multiplier)
      const accommodation = Math.round(baseDaily * 0.45 * days * Math.max(1, Math.round(travelers / 2)) * multiplier)
      const transport = Math.round(baseDaily * 0.15 * days * travelers * multiplier)
      const activities = Math.round(baseDaily * 0.1 * days * travelers * multiplier)
      const total = food + accommodation + transport + activities

      return {
        data: {
          total_budget_usd: total,
          estimated_total: total,
          total: total,
          daily_cost_usd: Math.round(total / days),
          city: String(destInput).replace(/[^a-zA-Z0-9\s,-]/g, "").trim() || "Nepal Destination",
          travelers: travelers,
          days: days,
          tier_label: tierLabel,
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
  },

  getSummary: () =>
    axiosClient.get("/budget/summary/")
}

export default budgetApi
