import { useForm } from "react-hook-form"
import { useEffect, useState } from "react"
import { FiCamera, FiUser } from "react-icons/fi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"
import PageHeader from "../components/common/PageHeader"

const Profile = () => {
  const { user, setUser } = useAuth()
  const { showToast } = useToast()
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm()
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    userApi
      .getProfile()
      .then(({ data }) => reset(data))
      .catch(() => reset(user || {}))
      .finally(() => setLoading(false))
  }, [])

  const onSubmit = async (data) => {
    try {
      const { data: updated } = await userApi.updateProfile(data)
      setUser(updated)
      showToast("Profile updated successfully", "success")
    } catch (err) {
      showToast(err?.response?.data?.message || "Update failed", "error")
    }
  }

  if (loading) return <Loader />

  return (
    <div className="max-w-2xl">
      <PageHeader title="My Profile" subtitle="Update your personal information and photo." icon={FiUser} theme="blue" />
      <div className="card-base p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="relative">
            <img
              src={user?.avatar || "https://api.dicebear.com/7.x/initials/svg?seed=" + (user?.name || "User")}
              alt="avatar"
              className="h-20 w-20 rounded-full object-cover border"
            />
            <button className="absolute bottom-0 right-0 bg-primary-500 text-white p-1.5 rounded-full">
              <FiCamera size={14} />
            </button>
          </div>
          <div>
            <p className="font-semibold">{user?.name}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="text-xs font-medium text-gray-500">Full Name</label>
            <input className="input-field mt-1" {...register("name")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Email</label>
            <input className="input-field mt-1" {...register("email")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Phone</label>
            <input className="input-field mt-1" {...register("phone")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Country</label>
            <input className="input-field mt-1" {...register("country")} />
          </div>
          <div className="sm:col-span-2">
            <label className="text-xs font-medium text-gray-500">Bio</label>
            <textarea rows={3} className="input-field mt-1" {...register("bio")} />
          </div>
          <div className="sm:col-span-2">
            <button type="submit" className="bg-blue-500 hover:bg-blue-600 text-white font-semibold px-5 py-2.5 rounded-xl transition" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Profile