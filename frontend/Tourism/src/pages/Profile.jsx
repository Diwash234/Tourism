import { useForm } from "react-hook-form"
import { useEffect, useState } from "react"
import { FiCamera } from "react-icons/fi"
import useAuth from "../hooks/useAuth"
import useToast from "../hooks/useToast"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"

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
      <h1 className="text-2xl font-bold mb-6">My Profile</h1>
      <div className="card-base p-6">
        <div className="flex items-center gap-4 mb-6">
          <div className="relative">
            <img
              src={user?.avatar || "https://api.dicebear.com/7.x/initials/svg?seed=" + (user?.first_name || "User")}
              alt="avatar"
              className="h-20 w-20 rounded-full object-cover border"
            />
            <button className="absolute bottom-0 right-0 bg-primary-500 text-white p-1.5 rounded-full">
              <FiCamera size={14} />
            </button>
          </div>
          <div>
            {/* FIXED: backend has no single `name` field — it's `first_name`/`last_name`. */}
            <p className="font-semibold">{user?.first_name} {user?.last_name}</p>
            <p className="text-sm text-gray-500">{user?.email}</p>
          </div>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          {/*
            FIXED: this form registered fields "name" and "phone", which
            don't exist on the backend's UserProfileSerializer at all — they
            were silently dropped on every save, so Name and Phone never
            actually persisted. The real fields are first_name, last_name,
            and phone_number. Also: email is read-only on the backend
            (auth-controlled), so it's shown but not submitted as editable.
          */}
          <div>
            <label className="text-xs font-medium text-gray-500">First Name</label>
            <input className="input-field mt-1" {...register("first_name")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Last Name</label>
            <input className="input-field mt-1" {...register("last_name")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Email</label>
            <input className="input-field mt-1" disabled {...register("email")} />
          </div>
          <div>
            <label className="text-xs font-medium text-gray-500">Phone</label>
            <input className="input-field mt-1" {...register("phone_number")} />
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
            <button type="submit" className="btn-primary" disabled={isSubmitting}>
              {isSubmitting ? "Saving..." : "Save Changes"}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

export default Profile