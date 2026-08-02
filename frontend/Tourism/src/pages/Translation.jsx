import { useEffect, useRef, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { motion } from "framer-motion"

import {
  FiRefreshCw,
  FiVolume2,
  FiMic,
  FiMicOff,
  FiWifiOff,
  FiCopy,
  FiHeart,
  FiRepeat,
} from "react-icons/fi"

import translationApi from "../api/translationApi"
import useToast from "../hooks/useToast"
import { getTranslationProvider } from "../utils/translationPreference"

const LANGUAGES = [
  { name: "English", code: "en" },
  { name: "Nepali", code: "ne" },
  { name: "Hindi", code: "hi" },
  { name: "Chinese", code: "zh" },
  { name: "French", code: "fr" },
  { name: "Spanish", code: "es" },
  { name: "German", code: "de" },
  { name: "Arabic", code: "ar" },
  { name: "Japanese", code: "ja" },
  { name: "Korean", code: "ko" },
  { name: "Russian", code: "ru" },
  { name: "Portuguese", code: "pt" },
  { name: "Italian", code: "it" },
  { name: "Thai", code: "th" },
  { name: "Vietnamese", code: "vi" },
  { name: "Indonesian", code: "id" },
  { name: "Newari", code: "new" },
  { name: "Sherpa", code: "xsr" },
  { name: "Maithili", code: "mai" },
  { name: "Bhojpuri", code: "bho" },
  { name: "Tamang", code: "tmg" },
]


const COMMON_PHRASES = [
  {
    en: "Hello",
    ne: "नमस्ते",
    pron: "Namaste"
  },
  {
    en: "Thank you",
    ne: "धन्यवाद",
    pron: "Dhanyabad"
  },
  {
    en: "Where is the hotel?",
    ne: "होटल कहाँ छ?",
    pron: "Hotel kaha cha?"
  },
  {
    en: "I need help",
    ne: "मलाई मद्दत चाहियो",
    pron: "Malai maddat chahiyo"
  },
  {
    en: "How much does this cost?",
    ne: "यो कति पर्छ?",
    pron: "Yo kati parcha?"
  },
  {
    en: "Call a doctor",
    ne: "डाक्टर बोलाउनुहोस्",
    pron: "Doctor bolaunuhos"
  }
]
const Translation = () => {

  const [searchParams] = useSearchParams()

  const [sourceText, setSourceText] = useState(() => {
    const place = searchParams.get("place")
    return place ? `I would like to visit ${place}` : ""
  })

  const [sourceLanguage, setSourceLanguage] = useState("auto")
  const [targetLang, setTargetLang] = useState("ne")

  const [translatedText, setTranslatedText] = useState("")
  const [loading, setLoading] = useState(false)

  const [isListening, setIsListening] = useState(false)
  const [voiceSupported, setVoiceSupported] = useState(true)

  const [isOffline, setIsOffline] = useState(!navigator.onLine)

  const [favorites, setFavorites] = useState(() => {
    return JSON.parse(
      localStorage.getItem("favorite_phrases") || "[]"
    )
  })


  const recognitionRef = useRef(null)

  const { showToast } = useToast()


  useEffect(() => {

    const SpeechRecognition =
      window.SpeechRecognition ||
      window.webkitSpeechRecognition


    if (!SpeechRecognition) {
      setVoiceSupported(false)
      return
    }


    const recognition = new SpeechRecognition()

    recognition.continuous = false
    recognition.interimResults = false


    recognition.onresult = (event) => {

      const text =
        event.results[0][0].transcript

      setSourceText(prev =>
        prev
          ? `${prev} ${text}`
          : text
      )
    }


    recognition.onerror = () => {
      showToast("Voice recognition failed", "error")
      setIsListening(false)
    }


    recognition.onend = () => {
      setIsListening(false)
    }


    recognitionRef.current = recognition


    return () => recognition.abort()


  }, [])



  useEffect(() => {

    const online = () => setIsOffline(false)
    const offline = () => setIsOffline(true)


    window.addEventListener("online", online)
    window.addEventListener("offline", offline)


    return () => {
      window.removeEventListener("online", online)
      window.removeEventListener("offline", offline)
    }

  }, [])



  const toggleVoice = () => {

    if (!recognitionRef.current)
      return


    if (isListening) {

      recognitionRef.current.stop()
      setIsListening(false)

    } else {

      recognitionRef.current.lang =
        navigator.language || "en-US"

      recognitionRef.current.start()
      setIsListening(true)

    }

  }
    const translate = async () => {

    if (!sourceText.trim()) {
      showToast("Enter text first", "error")
      return
    }


    if (isOffline) {
      showToast(
        "Offline mode enabled",
        "error"
      )
      return
    }


    try {

      setLoading(true)
      setTranslatedText("")


      const response =
        await translationApi.translateText({

          text: sourceText,

          source_language: sourceLanguage,

          target_language: targetLang,

          target_lang: targetLang,

          provider: getTranslationProvider()

        })


      const data = response.data


      setTranslatedText(
        data.translated_text ||
        data.translation ||
        data.result ||
        ""
      )


    } catch (error) {

      console.log(
        "Translation error:",
        error
      )

      showToast(
        "Translation failed",
        "error"
      )


    } finally {

      setLoading(false)

    }

  }



  const speak = (
    text,
    slow = false
  ) => {

    if (!window.speechSynthesis)
      return


    const speech =
      new SpeechSynthesisUtterance(text)


    speech.lang =
      targetLang === "ne"
        ? "ne-NP"
        : "en-US"


    speech.rate =
      slow ? 0.5 : 1


    window.speechSynthesis.speak(
      speech
    )

  }



  const copyText = () => {

    navigator.clipboard.writeText(
      translatedText
    )

    showToast(
      "Copied",
      "success"
    )

  }



  const saveFavorite = (phrase) => {


    const exists =
      favorites.some(
        item => item.en === phrase.en
      )


    let updated


    if (exists) {

      updated =
        favorites.filter(
          item =>
            item.en !== phrase.en
        )

    } else {

      updated = [
        ...favorites,
        phrase
      ]

    }


    setFavorites(updated)


    localStorage.setItem(
      "favorite_phrases",
      JSON.stringify(updated)
    )

  }



  const swapLanguage = () => {

    setTargetLang(
      targetLang === "ne"
        ? "en"
        : "ne"
    )

  }
    return (

    <div className="container-app py-10">


      <div className="flex justify-between items-center mb-3">

        <h1 className="section-title">
          🌎 AI Language Translator
        </h1>


        {isOffline && (

          <span className="text-xs bg-red-100 text-red-600 px-3 py-1 rounded-full flex items-center gap-2">

            <FiWifiOff />

            Offline

          </span>

        )}

      </div>



      <p className="text-gray-500 mb-8">

        Translate travel information,
        conversations and emergency messages.

      </p>




      <div className="grid lg:grid-cols-3 gap-6">



        <motion.div

          className="card-base p-6 space-y-6 lg:col-span-2"

          initial={{
            opacity:0,
            y:10
          }}

          animate={{
            opacity:1,
            y:0
          }}

        >


          <div className="flex justify-between">


            <label>
              Enter Text
            </label>


            {voiceSupported && (

              <button
                type="button"
                onClick={toggleVoice}
                className="text-himalaya-600"
              >

                {
                  isListening
                    ?
                    <FiMicOff />
                    :
                    <FiMic />
                }

              </button>

            )}

          </div>



          <textarea

            rows="6"

            className="input-field w-full"

            value={sourceText}

            onChange={
              e =>
              setSourceText(
                e.target.value
              )
            }

          />




          <div>


            <label>
              Translate To
            </label>


            <select

              className="input-field w-full mt-2"

              value={targetLang}

              onChange={
                e =>
                setTargetLang(
                  e.target.value
                )
              }

            >

              {
                LANGUAGES.map(
                  lang => (

                    <option
                      key={lang.code}
                      value={lang.code}
                    >

                      {lang.name}

                    </option>

                  )
                )
              }


            </select>



            <button

              type="button"

              onClick={swapLanguage}

              className="mt-3 text-sm flex gap-2 items-center text-himalaya-600"

            >

              <FiRepeat/>

              Swap Language

            </button>


          </div>




          <button

            type="button"

            onClick={translate}

            disabled={loading}

            className="btn-primary w-full flex justify-center gap-2"

          >

            <FiRefreshCw
              className={
                loading
                  ? "animate-spin"
                  : ""
              }
            />


            {
              loading
                ?
                "Translating..."
                :
                "Translate"
            }


          </button>




          {
            translatedText && (

              <div className="bg-himalaya-50 rounded-xl p-5">


                <div className="flex justify-between">


                  <h3 className="font-semibold">
                    Translation Result
                  </h3>


                  <div className="flex gap-3">


                    <button
                      type="button"
                      onClick={copyText}
                    >

                      <FiCopy />

                    </button>



                    <button
                      type="button"
                      onClick={() =>
                        speak(
                          translatedText
                        )
                      }
                    >

                      <FiVolume2 />

                    </button>


                  </div>


                </div>



                <p className="mt-3 text-lg">

                  {translatedText}

                </p>


              </div>

            )
          }


        </motion.div>





        <motion.div

          className="card-base p-6"

          initial={{
            opacity:0
          }}

          animate={{
            opacity:1
          }}

        >


          <h3 className="font-semibold mb-4">

            Offline Travel Phrases

          </h3>



          <div className="space-y-4">


            {
              COMMON_PHRASES.map(
                phrase => (

                  <div
                    key={phrase.en}
                    className="border-b pb-3"
                  >


                    <p className="font-medium">
                      {phrase.en}
                    </p>


                    <p className="text-himalaya-600">
                      {phrase.ne}
                    </p>



                    <div className="flex justify-between items-center">


                      <span className="text-xs italic">

                        {phrase.pron}

                      </span>



                      <button

                        type="button"

                        onClick={() =>
                          saveFavorite(
                            phrase
                          )
                        }

                      >

                        <FiHeart

                          className={
                            favorites.some(
                              f =>
                              f.en === phrase.en
                            )
                              ?
                              "text-red-500"
                              :
                              ""

                          }

                        />


                      </button>


                    </div>


                  </div>

                )
              )
            }


          </div>


        </motion.div>



      </div>


    </div>

  )

}


export default Translation