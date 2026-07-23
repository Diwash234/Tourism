import { useState } from "react";
import { FiRefreshCw, FiGlobe, FiCopy } from "react-icons/fi";
import { motion } from "framer-motion";
import translationApi from "../api/translationApi";
import useToast from "../hooks/useToast";
import PageHeader from "../components/common/PageHeader";
import { LANGUAGE_GROUPS } from "../utils/constants";

const QUICK_PHRASES = [
  "Where is the nearest hospital?",
  "How much does this cost?",
  "Can you help me, please?",
  "Where is the bus station?",
  "Is this water safe to drink?",
  "I am lost, please help.",
];

const Translation = () => {
  const [activeGroup, setActiveGroup] = useState(LANGUAGE_GROUPS[0]);
  const [sourceText, setSourceText] = useState("");
  const [targetLang, setTargetLang] = useState(LANGUAGE_GROUPS[0].languages[0]);
  const [result, setResult] = useState("");
  const [loading, setLoading] = useState(false);

  const { showToast } = useToast();

  const handleGroupChange = (group) => {
    setActiveGroup(group);
    setTargetLang(group.languages[0]);
  };

  const handleTranslate = async (text = sourceText) => {
    if (!text.trim()) {
      showToast("Please enter some text to translate.", "warning");
      return;
    }

    setSourceText(text);
    setLoading(true);

    try {
      const { data } = await translationApi.translateText({
        text,
        target_language: targetLang.code,
      });

      const translated =
        data.translatedText ||
        data.translated_text ||
        data.translation ||
        data.result ||
        data.text ||
        "";

      setResult(translated);

      if (!translated) {
        showToast("Translation completed, but no translated text was returned.", "warning");
      }
    } catch (error) {
      console.error("Translation Error:", error.response?.data || error);

      const errorMessage =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        "Translation service unavailable. Please try again shortly.";

      showToast(errorMessage, "error");
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = () => {
    if (!result) return;

    navigator.clipboard.writeText(result);
    showToast("Copied to clipboard", "success");
  };

  return (
    <div className="max-w-4xl mx-auto">
      <PageHeader
        title="Translate"
        subtitle="Communicate with locals in Nepal's regional languages, India's regional languages, or major international languages."
        icon={FiGlobe}
        theme="purple"
      />

      <div className="card-base p-6 space-y-5">
        <textarea
          rows={4}
          className="input-field"
          placeholder="Type text to translate..."
          value={sourceText}
          onChange={(e) => setSourceText(e.target.value)}
        />

        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">
            Quick phrases for travelers
          </p>

          <div className="flex flex-wrap gap-2">
            {QUICK_PHRASES.map((phrase) => (
              <button
                key={phrase}
                onClick={() => handleTranslate(phrase)}
                className="text-xs border border-gray-200 rounded-full px-3 py-1.5 hover:bg-gray-50 hover:border-primary-300 transition"
              >
                {phrase}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">
            Choose a country/region
          </p>

          <div className="flex gap-2 border-b border-gray-100">
            {LANGUAGE_GROUPS.map((group) => (
              <button
                key={group.key}
                onClick={() => handleGroupChange(group)}
                className={`px-4 py-2 text-sm font-semibold border-b-2 transition ${
                  activeGroup.key === group.key
                    ? "border-primary-500 text-primary-600"
                    : "border-transparent text-gray-400 hover:text-gray-600"
                }`}
              >
                {group.label}
              </button>
            ))}
          </div>
        </div>

        <div>
          <p className="text-xs font-medium text-gray-500 mb-2">
            Local languages in {activeGroup.label}
          </p>

          <div className="flex flex-wrap gap-2">
            {activeGroup.languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => setTargetLang(lang)}
                className={`text-sm rounded-xl px-3 py-2 border transition ${
                  targetLang.code === lang.code
                    ? "bg-purple-500 text-white border-purple-500"
                    : "border-gray-200 hover:border-purple-300 text-gray-700"
                }`}
              >
                {lang.label}
                <span className="opacity-70"> · {lang.native}</span>
              </button>
            ))}
          </div>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between pt-2">
          <p className="text-sm text-gray-500">
            Translating into{" "}
            <span className="font-semibold text-dark">
              {targetLang.label}
            </span>
          </p>

          <button
            onClick={() => handleTranslate()}
            disabled={loading}
            className="bg-purple-500 hover:bg-purple-600 disabled:opacity-60 text-white font-semibold px-5 py-2.5 rounded-xl transition flex items-center justify-center gap-2"
          >
            <FiRefreshCw className={loading ? "animate-spin" : ""} />
            {loading ? "Translating..." : "Translate"}
          </button>
        </div>

        {result && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-gray-50 rounded-xl p-4 text-sm text-dark border border-gray-100 flex items-start justify-between gap-3"
          >
            <span className="whitespace-pre-wrap">{result}</span>

            <button
              onClick={handleCopy}
              className="text-gray-400 hover:text-purple-500 shrink-0"
            >
              <FiCopy />
            </button>
          </motion.div>
        )}
      </div>
    </div>
  );
};

export default Translation;