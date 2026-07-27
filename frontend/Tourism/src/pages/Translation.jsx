// // CONFIRMED WORKING as-is — matches POST /translate/ exactly, and reads
// // response.data.translated_text which is exactly what the backend returns.
// import { useState } from "react"
// import { FiRefreshCw } from "react-icons/fi"
// import translationApi from "../api/translationApi"
// import useToast from "../hooks/useToast"


// const LANGUAGES = [
//   // Global Languages
//   { name: "English", code: "en" },
//   { name: "Nepali", code: "ne" },
//   { name: "Hindi", code: "hi" },
//   { name: "Chinese Simplified", code: "zh-CN" },
//   { name: "French", code: "fr" },
//   { name: "Spanish", code: "es" },
//   { name: "German", code: "de" },
//   { name: "Arabic", code: "ar" },
//   { name: "Japanese", code: "ja" },
//   { name: "Korean", code: "ko" },
//   { name: "Russian", code: "ru" },
//   { name: "Portuguese", code: "pt" },
//   { name: "Italian", code: "it" },
//   { name: "Thai", code: "th" },
//   { name: "Vietnamese", code: "vi" },
//   { name: "Indonesian", code: "id" },


//   // Nepal Regional Languages
//   { name: "Maithili", code: "mai" },
//   { name: "Bhojpuri", code: "bho" },
//   { name: "Tamang", code: "tmg" },
//   { name: "Gurung", code: "gvr" },
//   { name: "Magar", code: "mgp" },
//   { name: "Rai", code: "rai" },
//   { name: "Limbu", code: "lif" },
//   { name: "Newari (Nepal Bhasa)", code: "new" },
//   { name: "Tharu", code: "thl" },
//   { name: "Sherpa", code: "xsr" },
//   { name: "Doteli", code: "dty" },
//   { name: "Awadhi", code: "awa" },

// ]


// const Translation = () => {

//   const [sourceText, setSourceText] = useState("")
//   const [targetLang, setTargetLang] = useState("ne")
//   const [result, setResult] = useState("")
//   const [loading, setLoading] = useState(false)

//   const { showToast } = useToast()



//   const handleTranslate = async () => {

//     if (!sourceText.trim()) {
//       showToast(
//         "Please enter text to translate",
//         "error"
//       )
//       return
//     }


//     setLoading(true)
//     setResult("")


//     try {

//       const response = await translationApi.translateText({

//         text: sourceText,

//         target_language: targetLang,

//       })


//       setResult(
//         response.data.translated_text ||
//         response.data.translation ||
//         response.data.result ||
//         ""
//       )


//     } catch(error){

//       console.error(
//         error.response?.data || error
//       )


//       showToast(
//         "Translation failed. Please try again.",
//         "error"
//       )


//     } finally {

//       setLoading(false)

//     }

//   }



//   return (

//     <div className="max-w-4xl mx-auto">


//       <h1 className="text-2xl font-bold mb-6">
//         🌎 Universal Language Translator
//       </h1>



//       <div className="card-base p-6 space-y-5">


//         <textarea

//           rows={6}

//           className="input-field"

//           placeholder="Enter any language text..."

//           value={sourceText}

//           onChange={(e)=>
//             setSourceText(e.target.value)
//           }

//         />



//         <select

//           value={targetLang}

//           onChange={(e)=>
//             setTargetLang(e.target.value)
//           }

//           className="input-field"

//         >

//           {
//             LANGUAGES.map(language=>(

//               <option

//                 key={language.code}

//                 value={language.code}

//               >

//                 {language.name}

//               </option>

//             ))
//           }


//         </select>




//         <button

//           onClick={handleTranslate}

//           disabled={loading}

//           className="
//           btn-primary 
//           flex 
//           items-center 
//           justify-center 
//           gap-2
//           "

//         >

//           <FiRefreshCw

//             className={
//               loading
//               ? "animate-spin"
//               : ""
//             }

//           />


//           {
//             loading
//             ? "Translating..."
//             : "Translate"
//           }


//         </button>



//         {
//           result && (

//             <div
//               className="
//               bg-gray-50
//               border
//               rounded-xl
//               p-5
//               text-lg
//               "
//             >

//               {result}

//             </div>

//           )
//         }


//       </div>


//     </div>

//   )

// }


// export default Translation
import { useState } from "react"
import { FiRefreshCw, FiVolume2 } from "react-icons/fi"

import translationApi from "../api/translationApi"
import useToast from "../hooks/useToast"



const LANGUAGES = [

  {
    name: "English",
    code: "en"
  },

  {
    name: "Nepali",
    code: "ne"
  },

  {
    name: "Hindi",
    code: "hi"
  },

  {
    name: "Chinese",
    code: "zh"
  },

  {
    name: "French",
    code: "fr"
  },

  {
    name: "Spanish",
    code: "es"
  },

  {
    name: "German",
    code: "de"
  },

  {
    name: "Arabic",
    code: "ar"
  },

  {
    name: "Japanese",
    code: "ja"
  },

  {
    name: "Korean",
    code: "ko"
  },

  {
    name: "Russian",
    code: "ru"
  },

  {
    name: "Portuguese",
    code: "pt"
  },

  {
    name: "Italian",
    code: "it"
  },

  {
    name: "Thai",
    code: "th"
  },

  {
    name: "Vietnamese",
    code: "vi"
  },

  {
    name: "Indonesian",
    code: "id"
  }

]



const Translation = () => {


  const [sourceText,setSourceText] = useState("")

  const [targetLang,setTargetLang] = useState("ne")

  const [translatedText,setTranslatedText] = useState("")

  const [loading,setLoading] = useState(false)


  const {
    showToast
  } = useToast()





  const handleTranslate = async()=>{


    if(!sourceText.trim()){


      showToast(
        "Please enter text to translate",
        "error"
      )


      return

    }





    try{


      setLoading(true)

      setTranslatedText("")



      const response =
      await translationApi.translateText({

        text:sourceText,

        target_language:targetLang,

        target_lang:targetLang,

        source_language:"auto"

      })





      const data =
      response.data





      setTranslatedText(

        data.translated_text ||

        data.translation ||

        data.result ||

        ""

      )





    }

    catch(error){


      console.log(
        "Translation error:",
        error.response?.data || error.message
      )


      showToast(
        "Translation failed",
        "error"
      )


    }

    finally{


      setLoading(false)


    }



  }





  const speakText = (text)=>{


    if(
      !window.speechSynthesis ||
      !text
    )

    return



    const speech =
    new SpeechSynthesisUtterance(text)


    window.speechSynthesis.speak(
      speech
    )


  }






  return (


    <div className="container-app py-10">





      <h1 className="section-title mb-2">

        🌎 AI Language Translator

      </h1>




      <p className="text-gray-500 text-sm mb-8">

        Translate travel information, directions and conversations into different languages.

      </p>







      <div className="card-base p-6 space-y-6">





        <div>


          <label className="block text-sm font-medium mb-2">

            Enter Text

          </label>



          <textarea

            rows={6}

            className="input-field w-full"

            placeholder="Enter text here..."

            value={sourceText}

            onChange={
              (e)=>
              setSourceText(
                e.target.value
              )
            }

          />


        </div>







        <div>


          <label className="block text-sm font-medium mb-2">

            Translate To

          </label>



          <select


            className="input-field w-full"


            value={targetLang}


            onChange={
              (e)=>
              setTargetLang(
                e.target.value
              )
            }


          >



            {
              LANGUAGES.map(
                (language)=>(

                  <option

                    key={
                      language.code
                    }

                    value={
                      language.code
                    }

                  >

                    {
                      language.name
                    }

                  </option>


                )
              )
            }



          </select>



        </div>







        <button


          onClick={handleTranslate}


          disabled={loading}


          className="
          btn-primary
          flex
          items-center
          justify-center
          gap-2
          w-full
          "


        >



          <FiRefreshCw

            className={
              loading
              ?
              "animate-spin"
              :
              ""
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



            <div

              className="
              bg-gray-50
              border
              rounded-xl
              p-5
              "

            >



              <div className="flex justify-between items-center mb-3">



                <h3 className="font-semibold">

                  Translation Result

                </h3>



                <button


                  onClick={
                    ()=>speakText(
                      translatedText
                    )
                  }


                  className="
                  p-2
                  rounded-full
                  hover:bg-gray-200
                  "

                >


                  <FiVolume2 />



                </button>




              </div>





              <p className="text-lg">

                {
                  translatedText
                }

              </p>





            </div>



          )
        }





      </div>






    </div>


  )


}



export default Translation