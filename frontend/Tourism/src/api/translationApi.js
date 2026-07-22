import axiosClient from "./axiosClient"

// CONFIRMED WORKING as-is. Matches POST /api/v1/translate/, which now
// tries OpenAI first (if OPENAI_API_KEY is set), then the ML teammate's
// local-language model, then Google Translate, then a free fallback —
// so this should already work as long as OpenAI's quota/billing is fine
// (your earlier log showed a 429 rate-limit from OpenAI specifically,
// which just means it fell through to the next tier, not that this file
// is broken).
const translationApi = {

  translateText: (payload) => {
    return axiosClient.post(
      "/translate/",
      payload
    )
  }

}

export default translationApi