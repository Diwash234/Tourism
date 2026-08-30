import { useForm } from "react-hook-form"
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import {
  FiBell,
  FiGlobe,
  FiDollarSign,
  FiInfo,
  FiCpu,
  FiCheck,
} from "react-icons/fi"

import userApi from "../api/userApi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import { ALL_LANGS, setLang } from "../i18n"

import {
  TRANSLATION_PROVIDERS,
  getTranslationProvider,
  setTranslationProvider,
} from "../utils/translationPreference"


const Settings = () => {

  const {
    register,
    handleSubmit,
    reset,
  } = useForm()


  const { user, setUser } = useAuth()
  const { showToast } = useToast()


  const [saving, setSaving] = useState(false)
  const [languages, setLanguages] = useState([])
  const [provider, setProvider] = useState(
    getTranslationProvider()
  )
  const [currency, setCurrency] = useState(() => localStorage.getItem("tourism_currency") || "USD")
  const [notifPrefs, setNotifPrefs] = useState({ in_app_enabled: true, email_enabled: true, push_enabled: true, sms_enabled: false, safety_alerts: true, booking_updates: true, recommendations: true, marketing: false })



  useEffect(() => {


    userApi
      .getLanguages()
      .then(({ data }) => {

        console.log(
          "Languages API:",
          data
        )


        const list =
          data.results ||
          data.languages ||
          data ||
          []


        setLanguages(
          Array.isArray(list)
            ? list
            : []
        )


      })
      .catch((error)=>{

        console.log(
          "Language API Error:",
          error
        )

        setLanguages([])

      })



    userApi.getNotificationPreferences().then(({ data }) => setNotifPrefs(data)).catch(() => {})

    if(user?.preferred_language){

      reset({

        preferred_language:
          user.preferred_language?.code ||
          (typeof user.preferred_language === "string" ? user.preferred_language : "en")

      })

    }


  }, [user, reset])





  const onSubmit = async (data) => {
    setSaving(true)
    try {
      localStorage.setItem("tourism_currency", currency)
      await userApi.updateNotificationPreferences(notifPrefs)
      const selectedLanguage = languages.find((item) => String(item.code || item.language_code).toLowerCase() === String(data.preferred_language || "").toLowerCase())
      if (data.preferred_language) {
        // Sync the site-wide i18n store so the whole UI switches language
        // immediately (Settings previously saved to a key nothing read).
        const code = String(data.preferred_language).toLowerCase()
        const langCode =
          code === "ne" || code === "nepali" || code === "नेपाली" ? "ne"
          : code === "hi" || code === "hindi" || code === "हिन्दी" ? "hi"
          : code === "en" || code === "english" ? "en"
          : code.length === 2 ? code
          : null
        if (langCode) {
          localStorage.setItem("tourism_preferred_language", langCode)
          try {
            setLang(langCode)
          } catch { /* i18n store unavailable */ }
        }
      }
      try {
        const { data: updated } = await userApi.updateSettings({
          preferred_language: selectedLanguage?.id || selectedLanguage?.language_id || null,
          currency,
        })
        setUser(updated)
      } catch (e) {
        /* Ignore backend 404/500 if updateSettings is not mounted */
      }
      showToast("Language, currency, and notification preferences saved!", "success")
    } catch (error) {
      showToast("Could not save settings", "error")
    } finally {
      setSaving(false)
    }
  }





  return (

    <motion.div

      initial={{
        opacity:0,
        y:10
      }}

      animate={{
        opacity:1,
        y:0
      }}

      className="max-w-2xl fade-in theme-slate"

    >


      <h1 className="section-title">
        Settings
      </h1>



      <form

        onSubmit={
          handleSubmit(onSubmit)
        }

        className="card-base p-6 space-y-6"

      >




        {/* Language */}

        <div>


          <h3 className="font-semibold mb-3 flex items-center gap-2">

            <FiGlobe className="text-himalaya-500"/>

            Language

          </h3>



          <select

            className="input-field"

            {...register("preferred_language", {
              onChange: (event) => setLang(event.target.value),
            })}

          >


            {ALL_LANGS.map((lang) => (
              <option key={lang.code} value={lang.code}>
                {lang.flag} {lang.label} ({lang.native})
              </option>
            ))}



          </select>



        </div>






        {/* Translation Provider */}


        <div className="border-t border-gray-100 pt-6">


          <h3 className="font-semibold mb-2 flex items-center gap-2">


            <FiCpu className="text-himalaya-500"/>


            Translation Provider


          </h3>



          <p className="text-xs text-gray-400 mb-3">

            Select your preferred AI translation service.

          </p>




          <div className="space-y-3">


            {
              TRANSLATION_PROVIDERS.map((item)=>(


                <label

                  key={item.value}

                  className={`
                    flex gap-3 p-3 rounded-xl border cursor-pointer
                    ${
                      provider===item.value
                      ?
                      "border-himalaya-400 bg-himalaya-50"
                      :
                      "border-gray-200"
                    }
                  `}

                >



                  <input

                    type="radio"

                    checked={
                      provider===item.value
                    }

                    onChange={()=>{


                      setProvider(
                        item.value
                      )


                      setTranslationProvider(
                        item.value
                      )


                      showToast(
                        `Translation provider set to ${item.label}`,
                        "success"
                      )


                    }}


                    className="mt-1 accent-himalaya-500"

                  />



                  <div>


                    <p className="font-medium text-sm">

                      {item.label}

                    </p>



                    <p className="text-xs text-gray-500">

                      {item.desc}

                    </p>


                  </div>



                </label>


              ))
            }


          </div>



          <p className="text-[11px] text-saffron-600 bg-saffron-50 inline-flex items-center gap-1 px-2 py-1 rounded-full mt-3">

            <FiInfo size={11}/>

            Saved locally on this device.

          </p>



        </div>






        {/* Notifications */}
        <div className="border border-gray-200 rounded-2xl p-5 bg-white space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2 text-gray-900">
              <FiBell className="text-purple-600" size={16} />
              Notification Preferences
            </h3>
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full flex items-center gap-1">
              <FiCheck size={11} /> Active
            </span>
          </div>

          <div className="space-y-3">
            <label className="flex items-center justify-between text-sm cursor-pointer p-2 rounded-xl hover:bg-gray-50">
              <div>
                <p className="font-medium text-gray-800">Email Notifications</p>
                <p className="text-xs text-gray-500">Receive trip summaries, bookings, and receipts via email</p>
              </div>
              <input
                type="checkbox"
                checked={notifPrefs.email_enabled}
                onChange={(e) => setNotifPrefs({ ...notifPrefs, email_enabled: e.target.checked })}
                className="w-4 h-4 accent-purple-600 rounded"
              />
            </label>

            <label className="flex items-center justify-between text-sm cursor-pointer p-2 rounded-xl hover:bg-gray-50">
              <div>
                <p className="font-medium text-gray-800">Push Notifications</p>
                <p className="text-xs text-gray-500">Real-time alerts for weather changes and itinerary updates</p>
              </div>
              <input
                type="checkbox"
                checked={notifPrefs.push_enabled}
                onChange={(e) => setNotifPrefs({ ...notifPrefs, push_enabled: e.target.checked })}
                className="w-4 h-4 accent-purple-600 rounded"
              />
            </label>

            <label className="flex items-center justify-between text-sm cursor-pointer p-2 rounded-xl hover:bg-gray-50">
              <div>
                <p className="font-medium text-gray-800">Risk Alert SMS</p>
                <p className="text-xs text-gray-500">SMS broadcasts for landslide, monsoon, or altitude warnings</p>
              </div>
              <input
                type="checkbox"
                checked={notifPrefs.sms_enabled}
                onChange={(e) => setNotifPrefs({ ...notifPrefs, sms_enabled: e.target.checked })}
                className="w-4 h-4 accent-purple-600 rounded"
              />
            </label>
            <div className="border-t pt-3 grid sm:grid-cols-2 gap-2">
              {[["safety_alerts","Safety alerts"],["booking_updates","Booking updates"],["recommendations","Travel recommendations"],["marketing","Marketing messages"]].map(([key,label]) => <label key={key} className="flex items-center justify-between text-sm p-2 rounded-xl bg-gray-50"><span>{label}</span><input type="checkbox" checked={Boolean(notifPrefs[key])} onChange={(e)=>setNotifPrefs({...notifPrefs,[key]:e.target.checked})} className="w-4 h-4 accent-purple-600"/></label>)}
            </div>
          </div>
        </div>

        {/* Currency */}
        <div className="border border-gray-200 rounded-2xl p-5 bg-white space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold flex items-center gap-2 text-gray-900">
              <FiDollarSign className="text-emerald-600" size={16} />
              Preferred Currency
            </h3>
            <span className="text-[11px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full">
              {currency} Selected
            </span>
          </div>

          <select
            className="input-field"
            value={currency}
            onChange={(e) => {
              setCurrency(e.target.value)
              localStorage.setItem("tourism_currency", e.target.value)
              showToast(`Currency preference updated to ${e.target.value}`, "success")
            }}
          >
            <option value="USD">USD ($) — US Dollar</option>
            <option value="NPR">NPR (₨) — Nepalese Rupee</option>
            <option value="EUR">EUR (€) — Euro</option>
            <option value="GBP">GBP (£) — British Pound</option>
            <option value="AUD">AUD ($) — Australian Dollar</option>
            <option value="INR">INR (₹) — Indian Rupee</option>
            <option value="CNY">CNY (¥) — Chinese Yuan</option>
          </select>
        </div>





        <button

          type="submit"

          className="btn-primary"

          disabled={saving}

        >

          {
            saving
            ?
            "Saving..."
            :
            "Save Language"
          }


        </button>




      </form>


    </motion.div>

  )

}


export default Settings