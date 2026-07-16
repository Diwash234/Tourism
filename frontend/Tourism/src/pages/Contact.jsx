import { useForm } from "react-hook-form"
import { FiMail, FiPhone, FiMapPin } from "react-icons/fi"
import useToast from "../hooks/useToast"

const Contact = () => {
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm()
  const { showToast } = useToast()

  const onSubmit = async (data) => {
    // Replace with contactApi.send(data) once backend endpoint is available
    await new Promise((r) => setTimeout(r, 800))
    showToast("Message sent successfully!", "success")
    reset()
  }

  return (
    <div className="container-app py-16 grid grid-cols-1 md:grid-cols-2 gap-10">
      <div>
        <h1 className="section-title">Get in Touch</h1>
        <p className="text-gray-500 mb-8">Have questions about a destination or need support? Reach out to us.</p>
        <div className="space-y-4 text-sm text-gray-600">
          <p className="flex items-center gap-3"><FiMail className="text-primary-500" /> support@tourists.app</p>
          <p className="flex items-center gap-3"><FiPhone className="text-primary-500" /> +977-000-0000</p>
          <p className="flex items-center gap-3"><FiMapPin className="text-primary-500" /> Pokhara, Gandaki, Nepal</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="card-base p-6 space-y-4">
        <div>
          <input className="input-field" placeholder="Your Name" {...register("name", { required: true })} />
          {errors.name && <p className="text-xs text-red-500 mt-1">Name is required</p>}
        </div>
        <div>
          <input className="input-field" placeholder="Email Address" {...register("email", { required: true })} />
          {errors.email && <p className="text-xs text-red-500 mt-1">Email is required</p>}
        </div>
        <div>
          <textarea rows={5} className="input-field" placeholder="Your Message" {...register("message", { required: true })} />
          {errors.message && <p className="text-xs text-red-500 mt-1">Message is required</p>}
        </div>
        <button type="submit" className="btn-primary w-full" disabled={isSubmitting}>
          {isSubmitting ? "Sending..." : "Send Message"}
        </button>
      </form>
    </div>
  )
}

export default Contact