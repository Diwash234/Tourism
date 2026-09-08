import { useForm } from "react-hook-form"
import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { useTranslation } from "react-i18next"
import {
  FiBell,
  FiGlobe,
  FiDollarSign,
  FiInfo,
  FiCpu,
} from "react-icons/fi"

import userApi from "../api/userApi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"

import { SUPPORTED_LANGUAGES } from "../i18n"

import {
  TRANSLATION_PROVIDERS,
  getTranslationProvider,
  setTranslationProvider,
} from "../utils/translationPreference"


const Settings = () => {

  const { t, i18n } = useTranslation()

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



    if(user?.preferred_language){

      reset({

        preferred_language:
          user.preferred_language?.id ||
          user.preferred_language

      })

    }


  }, [user, reset])





  const onSubmit = async(data)=>{


    setSaving(true)


    try{


      const {data:updated} =
        await userApi.updateSettings({

          preferred_language:
            data.preferred_language || null

        })


      setUser(updated)


      showToast(
        "Language preference saved",
        "success"
      )


    }catch(error){


      console.log(
        "Save settings error:",
        error
      )


      showToast(
        "Could not save settings",
        "error"
      )


    }finally{

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
        {t("settings.title")}
      </h1>



      <form

        onSubmit={
          handleSubmit(onSubmit)
        }

        className="card-base p-6 space-y-6"

      >



        {/* Website Language -- ADDED. This is the piece that was
            actually missing: the "Language" dropdown further down
            saves a preference to the backend for translating
            destination CONTENT (descriptions etc, a separate existing
            feature -- see Translation.jsx), but nothing previously
            read any preference back to change the SITE'S OWN text.
            This one calls i18n.changeLanguage() directly, so the
            navbar/sidebar/footer (and this page) switch language
            immediately, and persists via localStorage so it's still
            set next time you visit -- no page reload needed. */}

        <div>

          <h3 className="font-semibold mb-1 flex items-center gap-2">

            <FiGlobe className="text-himalaya-500"/>

            {t("settings.websiteLanguage")}

          </h3>

          <p className="text-xs text-gray-400 mb-3">
            {t("settings.websiteLanguageDescription")}
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">

            {SUPPORTED_LANGUAGES.map((lang) => (

              <button

                key={lang.code}

                type="button"

                onClick={() => {
                  i18n.changeLanguage(lang.code)
                  showToast(`${lang.nativeLabel} / ${lang.label}`, "success")
                }}

                className={`
                  text-sm px-3 py-2 rounded-xl border text-left transition-colors
                  ${
                    i18n.language === lang.code
                      ? "border-himalaya-400 bg-himalaya-50 font-medium"
                      : "border-gray-200 hover:border-gray-300"
                  }
                `}

              >
                {lang.nativeLabel}
                <span className="block text-[11px] text-gray-400">{lang.label}</span>
              </button>

            ))}

          </div>

        </div>




        {/* Content Translation -- unchanged feature, just relabeled
            to distinguish it from Website Language above. */}

        <div className="border-t border-gray-100 pt-6">

          <h3 className="font-semibold mb-1 flex items-center gap-2 text-gray-500">
            {t("settings.contentTranslation")}
          </h3>

        </div>


        {/* Language */}

        <div>


          <h3 className="font-semibold mb-3 flex items-center gap-2">

            <FiGlobe className="text-himalaya-500"/>

            {t("settings.language")}

          </h3>



          <select

            className="input-field"

            {...register(
              "preferred_language"
            )}

          >


            <option value="">

              {
                languages.length
                  ?
                  "Select a language"
                  :
                  "No languages available"
              }

            </option>



            {
              languages.map((lang)=>(


                <option

                  key={
                    lang.id ||
                    lang.language_id
                  }

                  value={
                    lang.id ||
                    lang.language_id
                  }

                >

                  {
                    lang.name ||
                    lang.language_name
                  }

                </option>


              ))
            }



          </select>



        </div>






        {/* Translation Provider */}


        <div className="border-t border-gray-100 pt-6">


          <h3 className="font-semibold mb-2 flex items-center gap-2">


            <FiCpu className="text-himalaya-500"/>


            {t("settings.translationProvider")}


          </h3>



          <p className="text-xs text-gray-400 mb-3">

            {t("settings.translationProviderDescription")}

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

            {t("settings.savedLocally")}

          </p>



        </div>






        {/* Notifications */}


        <div className="border border-dashed border-gray-200 rounded-xl p-4">


          <h3 className="font-semibold mb-3 flex items-center gap-2 text-gray-500">


            <FiBell size={16}/>

            {t("settings.notifications")}


            <span className="ml-auto text-[11px] text-saffron-600 bg-saffron-50 px-2 py-1 rounded-full">

              {t("settings.notSavedYet")}

            </span>


          </h3>



          <div className="space-y-3 opacity-60">


            <label className="flex justify-between text-sm">

              Email Notifications

              <input
                type="checkbox"
                defaultChecked
                disabled
              />

            </label>



            <label className="flex justify-between text-sm">

              Push Notifications

              <input
                type="checkbox"
                defaultChecked
                disabled
              />

            </label>



            <label className="flex justify-between text-sm">

              Risk Alert SMS

              <input
                type="checkbox"
                disabled
              />

            </label>



          </div>


        </div>






        {/* Currency */}


        <div className="border border-dashed border-gray-200 rounded-xl p-4 opacity-60">


          <h3 className="font-semibold mb-3 flex items-center gap-2 text-gray-500">


            <FiDollarSign size={16}/>

            {t("settings.currency")}


            <span className="ml-auto text-[11px] text-saffron-600 bg-saffron-50 px-2 py-1 rounded-full">

              {t("settings.notSavedYet")}

            </span>


          </h3>



          <select className="input-field" disabled>

            <option>
              USD ($)
            </option>

            <option>
              NPR (₨)
            </option>

            <option>
              EUR (€)
            </option>


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
            t("settings.saving")
            :
            t("settings.saveLanguage")
          }


        </button>




      </form>


    </motion.div>

  )

}


export default Settings