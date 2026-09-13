/**
 * ML Service Client for Frontend
 * Routes through the Django API gateway (/api/v1/ml/ or /api/v1/...) so it works
 * seamlessly in browser previews without direct cross-origin localhost dependencies.
 */
import axiosClient from "../api/axiosClient"

// Recommendation
export async function getRecommendations(interest) {
  try {
    const res = await axiosClient.post("/ml/recommendations/", {
      interest: interest,
      top_n: 10,
    })
    return res.data
  } catch (err) {
    // Fallback to personalized recommendations endpoint
    const fallback = await axiosClient.get("/recommendations/personalized", {
      params: { interest },
    })
    return fallback.data
  }
}

// Risk prediction
export async function getRisk(data) {
  const res = await axiosClient.post("/ml/safety/", data)
  return res.data
}

// Emergency nearest facilities
export async function getEmergency(lat, lon, category = "hospital") {
  const res = await axiosClient.get("/emergency/contacts", {
    params: { lat, lon, category },
  })
  return res.data
}

// Budget prediction
export async function predictBudget(data) {
  const res = await axiosClient.post("/ml/budget/", data)
  return res.data
}

// Translation
export async function translateText(text, target_lang = "ne") {
  const res = await axiosClient.post("/translate/", {
    text: text,
    target_lang: target_lang,
  })
  return res.data
}

export default {
  getRecommendations,
  getRisk,
  getEmergency,
  predictBudget,
  translateText,
}
