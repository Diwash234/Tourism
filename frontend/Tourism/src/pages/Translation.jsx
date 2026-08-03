import { useEffect, useRef, useState } from "react"
import { useSearchParams } from "react-router-dom"
import { motion } from "framer-motion"

import Select from "react-select"

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

import { LANGUAGES } from "../data/languages"
import { COMMON_PHRASES } from "../data/phrases"



const Translation = () => {


const [searchParams] = useSearchParams()



const [sourceText,setSourceText] = useState(()=>{

const place =
searchParams.get("place")


return place
?
`I would like to visit ${place}`
:
""

})



const [sourceLanguage,setSourceLanguage] =
useState("auto")


const [targetLang,setTargetLang] =
useState("ne")



const [translatedText,setTranslatedText] =
useState("")



const [loading,setLoading] =
useState(false)



const [isListening,setIsListening] =
useState(false)



const [voiceSupported,setVoiceSupported] =
useState(true)



const [isOffline,setIsOffline] =
useState(!navigator.onLine)



const [favorites,setFavorites] =
useState(()=>{

return JSON.parse(
localStorage.getItem(
"favorite_phrases"
) || "[]"
)

})



const recognitionRef =
useRef(null)



const {
showToast
}=useToast()






/*
-------------------------
VOICE RECOGNITION
-------------------------
*/


useEffect(()=>{


const SpeechRecognition =
window.SpeechRecognition ||
window.webkitSpeechRecognition



if(!SpeechRecognition){

setVoiceSupported(false)

return

}



const recognition =
new SpeechRecognition()



recognition.continuous=false

recognition.interimResults=true



recognition.onresult=(event)=>{


const text =
Array.from(
event.results
)
.map(
result =>
result[0].transcript
)
.join("")



setSourceText(
prev =>
prev
?
`${prev} ${text}`
:
text
)


}



recognition.onerror=()=>{


showToast(
"Voice recognition failed",
"error"
)


setIsListening(false)


}



recognition.onend=()=>{


setIsListening(false)


}




recognitionRef.current =
recognition




return()=>{


recognition.abort()


}



},[])







/*
-------------------------
NETWORK STATUS
-------------------------
*/


useEffect(()=>{


const online=()=>setIsOffline(false)

const offline=()=>setIsOffline(true)



window.addEventListener(
"online",
online
)


window.addEventListener(
"offline",
offline
)




return()=>{


window.removeEventListener(
"online",
online
)


window.removeEventListener(
"offline",
offline
)



}



},[])








/*
-------------------------
START MICROPHONE
-------------------------
*/


const toggleVoice=()=>{


if(!recognitionRef.current)
return




if(isListening){


recognitionRef.current.stop()

setIsListening(false)


return


}




const speech =
LANGUAGES.find(
item =>
item.code===sourceLanguage
)?.speech
||
"en-US"



recognitionRef.current.lang =
speech



try{


recognitionRef.current.start()


setIsListening(true)



}catch(error){

console.log(error)

}



}










/*
-------------------------
TRANSLATE
-------------------------
*/


const translate=async()=>{


if(!sourceText.trim()){


showToast(
"Enter text first",
"error"
)


return

}




if(isOffline){


showToast(
"Offline mode enabled",
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


source_language:
sourceLanguage,


target_language:
targetLang,


target_lang:
targetLang,


provider:
getTranslationProvider()


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
"Translation error",
error
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









/*
-------------------------
TEXT SPEAKER
-------------------------
*/


const speak=(text,language)=>{


if(
!window.speechSynthesis ||
!text
)
return



const selected =
LANGUAGES.find(
item =>
item.code===language
)



const utterance =
new SpeechSynthesisUtterance(
text
)



utterance.lang =
selected?.speech
||
"en-US"



utterance.rate =
0.9



window.speechSynthesis.cancel()


window.speechSynthesis.speak(
utterance
)



}






/*
-------------------------
COPY
-------------------------
*/


const copyText=()=>{


navigator.clipboard.writeText(
translatedText
)



showToast(
"Copied",
"success"
)


}







/*
-------------------------
FAVORITES
-------------------------
*/


const saveFavorite=(phrase)=>{


const exists =
favorites.some(
item =>
item.id===phrase.id
)



let updated



if(exists){


updated =
favorites.filter(
item =>
item.id!==phrase.id
)



}
else{


updated=[
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






const swapLanguage=()=>{


const temp =
sourceLanguage



setSourceLanguage(
targetLang
)



setTargetLang(
temp==="auto"
?
"en"
:
temp
)



}





const languageOptions =
LANGUAGES.map(
language=>({

value:language.code,

label:language.name

})

)





// UI continues in Part 1B
return (

<div className="container-app py-10">


<div className="flex justify-between items-center mb-3">


<h1 className="section-title">
🌎 AI Language Translator
</h1>



{
isOffline &&

<span className="
text-xs 
bg-red-100 
text-red-600 
px-3 
py-1 
rounded-full 
flex 
items-center 
gap-2
">

<FiWifiOff/>

Offline

</span>

}



</div>





<p className="text-gray-500 mb-8">

Translate travel information,
conversations and emergency messages.

</p>







<div className="grid lg:grid-cols-3 gap-6">






<motion.div

className="
card-base 
p-6 
space-y-6 
lg:col-span-2
"

initial={{
opacity:0,
y:10
}}

animate={{
opacity:1,
y:0
}}

>






<div className="flex justify-between items-center">


<label className="font-medium">

Enter Text

</label>



{
voiceSupported &&


<button

type="button"

onClick={toggleVoice}

className="
text-himalaya-600 
flex 
items-center 
gap-2
"

>


{
isListening
?
<FiMicOff/>
:
<FiMic/>
}


{
isListening
?
"Listening..."
:
"Speak"
}


</button>


}



</div>







<textarea


rows="6"


className="
input-field 
w-full
"


value={sourceText}


onChange={
e=>
setSourceText(
e.target.value
)
}


/>








<div>


<label className="font-medium">

From Language

</label>



<Select


className="mt-2"


options={languageOptions}



value={
languageOptions.find(
item=>
item.value===sourceLanguage
)
||
{
value:"auto",
label:"Auto Detect"
}

}




onChange={
item=>
setSourceLanguage(
item.value
)
}




/>



</div>








<div>


<label className="font-medium">

Translate To

</label>



<Select


className="mt-2"


options={languageOptions}



value={
languageOptions.find(
item=>
item.value===targetLang
)
}



onChange={
item=>
setTargetLang(
item.value
)
}




/>



<button


type="button"


onClick={swapLanguage}


className="
mt-3 
text-sm 
text-himalaya-600 
flex 
items-center 
gap-2
"


>


<FiRepeat/>

Swap Language


</button>



</div>










<button


type="button"


onClick={translate}


disabled={loading}



className="
btn-primary 
w-full 
flex 
justify-center 
gap-2
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
translatedText &&



<div className="
bg-himalaya-50 
rounded-xl 
p-5
">


<div className="
flex 
justify-between 
items-center
">



<h3 className="font-semibold">

Translation Result

</h3>




<div className="
flex 
gap-4
">


<button

type="button"

onClick={copyText}

>

<FiCopy/>

</button>





<button

type="button"

onClick={()=>
speak(
translatedText,
targetLang
)
}

className="
text-himalaya-600
"

>


<FiVolume2/>

</button>



</div>




</div>







<div className="
mt-4 
text-lg 
flex 
items-center 
justify-between
">


<span>

{translatedText}

</span>



<button


onClick={()=>
speak(
translatedText,
targetLang
)
}


className="
ml-3
text-himalaya-600
"


>

<FiVolume2/>

</button>



</div>





</div>


}






</motion.div>














<motion.div


className="
card-base 
p-6
"


initial={{
opacity:0
}}


animate={{
opacity:1
}}


>


<h3 className="
font-semibold 
mb-4
">

Offline Travel Phrases

</h3>





<div className="space-y-5">



{

COMMON_PHRASES.map(
phrase=>(


<div

key={phrase.id}

className="
border-b 
pb-4
"

>



<div className="
flex 
justify-between 
items-center
">


<p className="font-medium">

{phrase.english}

</p>


<button

onClick={()=>
speak(
phrase.english,
"en"
)
}

className="
text-himalaya-600
"

>

<FiVolume2/>

</button>


</div>







<div className="
flex 
justify-between 
items-center
">


<p className="
text-himalaya-600
">

{phrase.translation}

</p>



<button

onClick={()=>
speak(
phrase.translation,
phrase.language
)
}

className="
text-himalaya-600
"

>

<FiVolume2/>

</button>



</div>







<p className="
text-xs 
italic 
text-gray-500
">


{phrase.pronunciation}



</p>







<div className="
flex 
justify-end
">


<button


onClick={()=>
saveFavorite(
phrase
)
}


>


<FiHeart


className={

favorites.some(
item=>
item.id===phrase.id
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