import { useState } from "react"
import { useForm } from "react-hook-form"
import { motion } from "framer-motion"
import { FiMail, FiPhone, FiMapPin } from "react-icons/fi"
import useToast from "../hooks/useToast"
import adminApi from "../api/adminApi"

const SUPPORT_EMAIL = "support@tourists.app"

const Contact = () => {

  const {
    register,
    handleSubmit,
    reset,
    getValues,
    formState:{errors,isSubmitting}
  } = useForm()

  const {showToast}=useToast()
  const [evidence, setEvidence] = useState([])


  const onSubmit = async () => {
    const { name, email, message, subject, category } = getValues()
    try {
      const body = new FormData()
      body.append("name", name || "")
      body.append("email", email || "")
      body.append("subject", subject || `Message from ${name || "visitor"}`)
      body.append("message", message)
      body.append("category", category || "correction")
      evidence.forEach((file) => body.append("evidence", file))
      await adminApi.sendFeedback(body)
      showToast("Your report and evidence were sent to the admin review queue.", "success")
      reset(); setEvidence([])
    } catch (e) {
      showToast(e?.response?.data?.detail || "Could not send message. Please try again.", "error")
    }
  }


return (

<div className="container-app py-16 grid grid-cols-1 md:grid-cols-2 gap-10 fade-in theme-indigo">


<motion.div
initial={{opacity:0,x:-10}}
animate={{opacity:1,x:0}}
>


<h1 className="section-title">
Get in Touch
</h1>


<p className="text-gray-500 mb-8">
Have questions about a destination or need support? Reach out to us.
</p>


<div className="space-y-4 text-sm text-gray-600">


<p className="flex items-center gap-3">
<FiMail className="text-himalaya-500"/>
{SUPPORT_EMAIL}
</p>


<p className="flex items-center gap-3">
<FiPhone className="text-himalaya-500"/>
+977-000-0000
</p>


<p className="flex items-center gap-3">
<FiMapPin className="text-himalaya-500"/>
Pokhara, Gandaki, Nepal
</p>


</div>

</motion.div>



<motion.form

initial={{opacity:0,x:10}}
animate={{opacity:1,x:0}}

onSubmit={handleSubmit(onSubmit)}

className="card-base p-6 space-y-4"

>


<div>

<input
className="input-field"
placeholder="Your Name"
{...register("name",{required:true})}
/>

{errors.name &&
<p className="text-xs text-nepalred-500 mt-1">
Name is required
</p>}

</div>



<div>

<input

className="input-field"

placeholder="Email Address"

{...register("email",{required:true})}

/>

{errors.email &&
<p className="text-xs text-nepalred-500 mt-1">
Email is required
</p>}

</div>



<div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
<input className="input-field" placeholder="Subject / place name" {...register("subject",{required:true})} />
<select className="input-field" {...register("category")}>
<option value="correction">Correct wrong information</option>
<option value="emergency_service">Emergency service feedback</option>
<option value="hotel_hospital">Hotel / hospital information</option>
<option value="route_distance">Route or distance problem</option>
<option value="risk_news">Risk / disaster news</option>
<option value="general">General feedback</option>
</select>
</div>

<div>

<textarea

rows={5}

className="input-field"

placeholder="Your Message"

{...register("message",{required:true})}

/>


{errors.message &&
<p className="text-xs text-nepalred-500 mt-1">
Message is required
</p>}


</div>



<label className="block rounded-xl border-2 border-dashed border-gray-200 p-4 text-center text-xs font-bold text-gray-500 cursor-pointer">
Evidence images/videos ({evidence.length}/8)
<input hidden type="file" multiple accept="image/*,video/*" onChange={(e) => setEvidence(Array.from(e.target.files).slice(0,8))} />
</label>

<button

type="submit"

className="btn-primary w-full"

disabled={isSubmitting}

>

{isSubmitting ? "Sending..." : "Send to Admin"}

</button>


<p className="text-xs text-gray-400 text-center">
Saved in the admin feedback queue for review and correction.
</p>


</motion.form>


</div>

)

}

export default Contact