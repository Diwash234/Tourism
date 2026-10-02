import axiosClient from "./axiosClient"

// Matches POST /api/v1/translate/. NOTE: I checked the backend directly
// (tourist/serializers.py TranslateRequestSerializer + views.py
// TranslateTextView) — `provider` is sent below but is NOT currently a
// field the serializer accepts, and the view doesn't pass one to
// translate_text() either, even though translate_text() itself fully
// supports provider="standard"/"gemini"/"groq"/"openai"/"auto" (see
// tourist/utils.py). So today, `provider` is silently dropped and the
// backend always uses its own "auto" tiered fallback regardless of what
// the user picks in Settings. Sending it anyway so this becomes fully
// functional the moment two small backend changes land:
//   1. Add `provider = serializers.CharField(required=False, default="auto")`
//      to TranslateRequestSerializer
//   2. Pass `serializer.validated_data.get("provider", "auto")` as the
//      4th arg to translate_text() in TranslateTextView.post()
const translationApi = {

  translateText: (payload) => {
    return axiosClient.post(
      "/translate/",
      payload
    )
  }

}

export default translationApi