import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { Link, useSearchParams } from "react-router-dom"
import {
  FiUsers, FiMapPin, FiAlertTriangle, FiDollarSign, FiCheck, FiX,
  FiEye, FiShield, FiActivity, FiImage, FiPlus, FiTrash2, FiEdit3,
  FiNavigation, FiPhoneCall, FiUserCheck, FiUserX, FiSearch, FiRefreshCw,
  FiClock, FiTrendingUp, FiLayers, FiFileText, FiCalendar, FiHome,
  FiCompass, FiInfo, FiChevronRight, FiExternalLink, FiPlay
} from "react-icons/fi"
import adminApi from "../../api/adminApi"
import adminPanelApi from "../../api/adminPanelApi"
import destinationApi from "../../api/destinationApi"
import Loader from "../../components/common/Loader"
import LineChartCard from "../../components/charts/LineChartCard"
import BarChartCard from "../../components/charts/BarChartCard"
import useToast from "../../hooks/useToast"
import useAuth from "../../hooks/useAuth"
import InfrastructureModerationPanel from "../../components/admin/InfrastructureModerationPanel"
import ServicePhotosPanel from "../../components/admin/ServicePhotosPanel"
import DataExplorerPanel from "../../components/admin/DataExplorerPanel"
import CMSPanel from "../../components/admin/CMSPanel"
import StaffPermissionsPanel from "../../components/admin/StaffPermissionsPanel"
import DestinationFeaturesPanel from "../../components/admin/DestinationFeaturesPanel"
import CategoryTranslationPanel from "../../components/admin/CategoryTranslationPanel"
import HotelBookingPanel from "../../components/admin/HotelBookingPanel"
import SafetyManagementPanel from "../../components/admin/SafetyManagementPanel"
import NotificationSettingsPanel from "../../components/admin/NotificationSettingsPanel"
import MediaLibraryPanel from "../../components/admin/MediaLibraryPanel"
import DatasetManagerPanel from "../../components/admin/DatasetManagerPanel"
import FeedbackWorkspace from "../../components/admin/FeedbackWorkspace"
import ReportsPanel from "../../components/admin/ReportsPanel"
import UserManagement from "../../components/admin/UserManagement"
import ReviewModerationPanel from "../../components/admin/ReviewModerationPanel"
import BrandingPanel from "../../components/admin/BrandingPanel"
import TravelServicesPanel from "../../components/admin/TravelServicesPanel"
import RetentionPolicyPanel from "../../components/admin/RetentionPolicyPanel"
import OwnerDeskPanel from "../../components/admin/OwnerDeskPanel"
import MarketplacePanel from "../../components/admin/MarketplacePanel"

const ROLES = [
  { id: "tourist", label: "Tourist / Traveler" },
  { id: "guide", label: "Local Guide" },
  { id: "staff", label: "Staff (Sub-Admin)" },
  { id: "content_moderator", label: "Content Moderator" },
  { id: "district_manager", label: "District Manager" },
  { id: "tourist_police", label: "Tourist Police" },
  { id: "hotel_manager", label: "Hotel Manager" },
  { id: "admin", label: "Admin" },
  { id: "super_admin", label: "Super Admin" },
]

const AdminDashboard = () => {
  const { user } = useAuth()
  const { showToast } = useToast()

  const [searchParams, setSearchParams] = useSearchParams()
  const activeTab = searchParams.get("section") || "overview"
  const setActiveTab = (section) => setSearchParams(section === "overview" ? {} : { section })
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  // Data states
  const [users, setUsers] = useState([])
  const [tracking, setTracking] = useState([])
  const [pendingPlaces, setPendingPlaces] = useState([])
  const [pendingImages, setPendingImages] = useState([])
  const [emergencies, setEmergencies] = useState([])
  const [expenseReports, setExpenseReports] = useState([])
  const [riskReports, setRiskReports] = useState([])
  const [categories, setCategories] = useState([])

  // Search / filter states
  const [userSearch, setUserSearch] = useState("")

  // Modal states
  const [showAddUserModal, setShowAddUserModal] = useState(false)
  const [newUserForm, setNewUserForm] = useState({
    email: "", password: "", first_name: "", last_name: "", role: "staff", managed_district: "", bio: ""
  })

  // Full detail inspection modal for place submission
  const [inspectingPlace, setInspectingPlace] = useState(null)
  const [editingPlace, setEditingPlace] = useState(null)
  const [placeEditForm, setPlaceEditForm] = useState({})

  // User detail travel history modal
  const [selectedUserHistory, setSelectedUserHistory] = useState(null)

  // Expense modal
  const [showAddExpenseModal, setShowAddExpenseModal] = useState(false)
  const [expenseForm, setExpenseForm] = useState({
    destination_name: "", num_people: 2, num_days: 5, travel_mode: "Tourist Bus",
    accommodation_cost: 120, travel_cost: 60, food_cost: 80, entry_cost: 30, extra_cost: 20,
    route_details: "Kathmandu to Pokhara via Prithvi Highway", notes: "Field survey data"
  })

  // AI Research state
  const [researchQuery, setResearchQuery] = useState("")
  const [researchResult, setResearchResult] = useState(null)
  const [isResearching, setIsResearching] = useState(false)

  // Place Intelligence & Mass Discovery staging state
  const [discoveryStats, setDiscoveryStats] = useState(null)
  const [healthReport, setHealthReport] = useState(null)
  const [candidates, setCandidates] = useState([])
  const [candidatesLoading, setCandidatesLoading] = useState(false)
  const [candidateFilterStatus, setCandidateFilterStatus] = useState("")
  const [candidateSearch, setCandidateSearch] = useState("")
  const [selectedCandidateIds, setSelectedCandidateIds] = useState([])
  const [batchForm, setBatchForm] = useState({ limit: 2500, province: "", district: "" })
  const [isRunningBatch, setIsRunningBatch] = useState(false)

  // Multi-Source Image Acquisition Pipeline state
  const [pipelineDestSlug, setPipelineDestSlug] = useState("phewa-lake-tal-barahi")
  const [pipelineImages, setPipelineImages] = useState([])
  const [pipelineLoading, setPipelineLoading] = useState(false)
  const [pipelineDestId, setPipelineDestId] = useState(null)
  const [newImageUrl, setNewImageUrl] = useState("")
  const [newImageCaption, setNewImageCaption] = useState("")
  const [newImageFile, setNewImageFile] = useState(null)
  const [pipelineVideos, setPipelineVideos] = useState([])
  const [newVideoFile, setNewVideoFile] = useState(null)

  const handleUploadAdminImage = async () => {
    if (!newImageFile) return
    const destId = await resolvePipelineDestination()
    if (!destId) return showToast("Select a destination first.", "error")
    const form = new FormData()
    form.append("image", newImageFile)
    form.append("caption", newImageCaption || newImageFile.name)
    form.append("is_cover", "true")
    try {
      await adminApi.addAdminDestinationImage(destId, form)
      showToast("Local image uploaded and set as cover.", "success")
      setNewImageFile(null); setNewImageCaption("")
      await loadPipelineImages(null, destId)
    } catch (error) {
      showToast(error?.response?.data?.detail || "Local image upload failed.", "error")
    }
  }

  const handleAddAdminImage = async () => {
    if (!newImageUrl.trim()) return
    const destId = await resolvePipelineDestination()
    if (!destId) return showToast("Select a destination first.", "error")
    try {
      await adminApi.addAdminDestinationImage(destId, {
        image_url: newImageUrl.trim(),
        caption: newImageCaption || undefined,
        is_cover: true,
        source: "admin",
        photographer: "Administrator",
        license: "Admin-provided",
      })
      showToast("Image added and set as cover.", "success")
      setNewImageUrl(""); setNewImageCaption("")
      await loadPipelineImages(null, destId)
    } catch {
      showToast("Could not add image. Check the URL and permissions.", "error")
    }
  }

  const handleSetAdminCover = async (imageId) => {
    if (!pipelineDestId) return
    try {
      await adminApi.setAdminDestinationCover(pipelineDestId, { image_id: imageId })
      showToast("Cover updated.", "success")
      loadPipelineImages()
    } catch {
      showToast("Could not update cover.", "error")
    }
  }

  const galleryRows = (gallery = []) => gallery.map((img) => ({
    id: img.id,
    url: img.url || img.external_url || img.image_url || img.display_url,
    caption: img.caption,
    author: img.photographer || img.author || "Administrator",
    source: img.source || img.source_platform || "admin",
    license: img.license || img.license_type || "",
    sourceUrl: img.source_url || img.sourceUrl,
    isAiGenerated: String(img.source || "").includes("ai") || img.isAiGenerated,
    is_cover: img.is_cover,
    verification_status: img.verification_status || img.status,
  }))

  const resolvePipelineDestination = async (slugToLoad = null, destId = null) => {
    if (destId) {
      setPipelineDestId(destId)
      return destId
    }
    const s = slugToLoad || pipelineDestSlug
    try {
      const { data } = await destinationApi.getById(s)
      if (data?.id) {
        setPipelineDestId(data.id)
        if (data.slug) setPipelineDestSlug(data.slug)
        return data.id
      }
    } catch { /* fall through to search */ }
    try {
      const { data } = await destinationApi.getAll({ search: s, page_size: 8 })
      const list = data.results || []
      const found = list.find((row) => row.slug === s || String(row.id) === String(s)) || list[0]
      if (found?.id) {
        setPipelineDestId(found.id)
        if (found.slug) setPipelineDestSlug(found.slug)
        return found.id
      }
    } catch { /* ignore */ }
    return pipelineDestId || null
  }

  const loadPipelineImages = async (slugToLoad = null, destId = null) => {
    const s = slugToLoad || pipelineDestSlug
    setPipelineLoading(true)
    try {
      const id = await resolvePipelineDestination(s, destId)
      if (id) {
        const { data } = await adminApi.getAdminDestination(id)
        setPipelineImages(galleryRows(data.gallery || []))
        setPipelineVideos(data.videos || [])
        if (data.slug) setPipelineDestSlug(data.slug)
      } else {
        const { data } = await adminApi.getDestinationImages(s)
        setPipelineImages(galleryRows(data.images || []))
      }
    } catch (e) {
      setPipelineImages([])
    } finally {
      setPipelineLoading(false)
    }
  }

  const handleDiscoverPipelineImages = async () => {
    setPipelineLoading(true)
    try {
      const { data } = await adminApi.discoverDestinationImages(pipelineDestSlug)
      setPipelineImages(data.images || [])
      showToast(data.message || "Multi-source image discovery completed!", "success")
    } catch (e) {
      showToast("Could not discover images", "error")
    } finally {
      setPipelineLoading(false)
    }
  }

  const handleRefreshPipelineImages = async () => {
    setPipelineLoading(true)
    try {
      const { data } = await adminApi.refreshDestinationImages(pipelineDestSlug)
      setPipelineImages(data.images || [])
      showToast(data.message || "Image collection refreshed!", "success")
    } catch (e) {
      showToast("Could not refresh images", "error")
    } finally {
      setPipelineLoading(false)
    }
  }

  // Free web image search (Wikimedia / DuckDuckGo / Openverse) for the
  // currently selected destination.
  const [webSearching, setWebSearching] = useState(false)
  const [webImageCount, setWebImageCount] = useState(50) // admin can add up to 50 images at once
  const [destSearch, setDestSearch] = useState("")
  const [destSearchResults, setDestSearchResults] = useState([])

  const handleFetchWebImages = async () => {
    if (!pipelineDestSlug) return
    setWebSearching(true)
    try {
      const { data } = await adminApi.fetchWebImages(pipelineDestSlug, webImageCount || 50)
      showToast(`${data.saved} real images saved for ${data.destination}`, "success")
      loadPipelineImages()
    } catch (e) {
      showToast(e?.response?.data?.detail || "Could not fetch web images", "error")
    } finally {
      setWebSearching(false)
    }
  }

  const [aiGenerating, setAiGenerating] = useState(false)
  const handleGenerateAIImages = async () => {
    if (!pipelineDestSlug) return
    setAiGenerating(true)
    try {
      const { data } = await adminApi.generateAIImages(pipelineDestSlug, 14)
      showToast(`${data.saved} AI images generated for ${data.destination}`, "success")
      loadPipelineImages()
    } catch (e) {
      showToast(e?.response?.data?.detail || "Could not generate AI images", "error")
    } finally {
      setAiGenerating(false)
    }
  }

  const handleDeleteImage = async (imageId) => {
    if (!confirm("Remove this image from the destination?")) return
    try {
      await adminApi.deleteDestinationImage(imageId)
      showToast("Image removed", "success")
      loadPipelineImages()
    } catch {
      showToast("Could not delete image", "error")
    }
  }

  const runDestinationSearch = async () => {
    if (!destSearch.trim()) return
    try {
      const { data } = await adminApi.getDestinations({ search: destSearch, page_size: 20 })
      setDestSearchResults(data.results || [])
    } catch {
      setDestSearchResults([])
    }
  }

  const fetchDiscoveryData = async () => {
    setCandidatesLoading(true)
    try {
      const [statsRes, reportRes, candRes] = await Promise.allSettled([
        adminApi.getDiscoveryStats(),
        adminApi.getDiscoveryHealthReport(),
        adminApi.getCandidates({ status: candidateFilterStatus, search: candidateSearch }),
      ])
      if (statsRes.status === "fulfilled") setDiscoveryStats(statsRes.value.data)
      if (reportRes.status === "fulfilled") setHealthReport(reportRes.value.data)
      if (candRes.status === "fulfilled") setCandidates(candRes.value.data.results || candRes.value.data || [])
    } catch (err) {
      console.error(err)
    } finally {
      setCandidatesLoading(false)
    }
  }

  const handleRunBatch = async () => {
    setIsRunningBatch(true)
    try {
      const { data } = await adminApi.runDiscoveryBatch(batchForm)
      showToast(`Discovery batch complete! Scanned ${data.summary?.scanned || 0}, Created ${data.summary?.created || 0}`, "success")
      fetchDiscoveryData()
      fetchAllData()
    } catch (err) {
      showToast("Discovery batch execution failed.", "error")
    } finally {
      setIsRunningBatch(false)
    }
  }

  const handleCandidateSingleAction = async (id, action, targetId = null) => {
    try {
      const { data } = await adminApi.candidateAction(id, { action, target_destination_id: targetId })
      showToast(data.message || `Action ${action} successful!`, "success")
      fetchDiscoveryData()
      fetchAllData()
    } catch (err) {
      showToast(err.response?.data?.detail || "Candidate action failed", "error")
    }
  }

  const handleCandidateBulkAction = async (action) => {
    if (!selectedCandidateIds.length) return showToast("Select at least one candidate first", "error")
    try {
      const { data } = await adminApi.candidateBulkAction({ candidate_ids: selectedCandidateIds, action })
      showToast(`Bulk ${action} completed: ${data.processed} processed.`, "success")
      setSelectedCandidateIds([])
      fetchDiscoveryData()
      fetchAllData()
    } catch (err) {
      showToast("Bulk operation failed.", "error")
    }
  }

  const handleTriggerResearch = async (queryToResearch = null) => {
    const q = queryToResearch || researchQuery.trim()
    if (!q) return showToast("Enter a destination name to research", "error")
    setIsResearching(true)
    try {
      const { data } = await destinationApi.researchDestination(q)
      setResearchResult(data)
      showToast(data.message || "Destination research complete!", "success")
      fetchAllData()
    } catch (err) {
      showToast("Research failed. Try another place name.", "error")
    } finally {
      setIsResearching(false)
    }
  }

  // Load all data
  const fetchAllData = async () => {
    setLoading(true)
    try {
      const [statsRes, usersRes, trackRes, placesRes, imagesRes, emergRes, expRes, riskRes, catRes] =
        await Promise.allSettled([
          adminApi.getStats(),
          adminApi.getUsers(),
          adminApi.getUserTracking(),
          adminApi.getPendingPlaces(),
          adminApi.getPendingImages(),
          adminApi.getEmergencies(),
          adminApi.getExpenseFeedbacks(),
          adminApi.getRiskFeedbacks(),
          destinationApi.getCategories(),
        ])

      if (statsRes.status === "fulfilled") setStats(statsRes.value.data)
      if (usersRes.status === "fulfilled") setUsers(usersRes.value.data)
      if (trackRes.status === "fulfilled") setTracking(trackRes.value.data)
      if (placesRes.status === "fulfilled") setPendingPlaces(placesRes.value.data)
      if (imagesRes.status === "fulfilled") setPendingImages(imagesRes.value.data)
      if (emergRes.status === "fulfilled") setEmergencies(emergRes.value.data)
      if (expRes.status === "fulfilled") setExpenseReports(expRes.value.data.results || expRes.value.data || [])
      if (riskRes.status === "fulfilled") setRiskReports(riskRes.value.data.results || riskRes.value.data || [])
      if (catRes.status === "fulfilled") setCategories(catRes.value.data.results || catRes.value.data || [])
    } catch (err) {
      console.error("Dashboard fetch error:", err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchAllData()
  }, [])

  useEffect(() => {
    if (activeTab === "image_pipeline") {
      loadPipelineImages()
    }
  }, [activeTab])

  // User Actions
  const handleCreateUser = async (e) => {
    e.preventDefault()
    try {
      await adminApi.createUser(newUserForm)
      showToast("User/Sub-Admin created successfully!", "success")
      setShowAddUserModal(false)
      setNewUserForm({ email: "", password: "", first_name: "", last_name: "", role: "staff", managed_district: "", bio: "" })
      fetchAllData()
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to create user", "error")
    }
  }

  const handleUpdateUserRole = async (userId, newRole) => {
    try {
      await adminApi.updateUser(userId, { role: newRole })
      showToast(`Role updated to ${newRole}`, "success")
      fetchAllData()
    } catch (err) {
      showToast("Failed to update role", "error")
    }
  }

  const handleToggleUserStatus = async (userId, currentStatus) => {
    try {
      await adminApi.updateUserStatus(userId, { is_active: !currentStatus })
      showToast(`User ${currentStatus ? "deactivated" : "activated"}`, "info")
      fetchAllData()
    } catch (err) {
      showToast("Failed to update status", "error")
    }
  }

  const handleDeleteUser = async (userId) => {
    if (!window.confirm("Are you sure you want to delete this user? This action cannot be undone.")) return
    try {
      await adminApi.deleteUser(userId)
      showToast("User removed successfully", "success")
      fetchAllData()
    } catch (err) {
      showToast(err.response?.data?.detail || "Failed to delete user", "error")
    }
  }

  // Place Approval Actions (GREEN = Accept, RED = Reject)
  const handleApprovePlace = async (placeId, customPayload = {}) => {
    try {
      await adminApi.approvePlace(placeId, customPayload)
      showToast("✅ Place ACCEPTED and published live into tourist_destination table!", "success")
      setInspectingPlace(null)
      setEditingPlace(null)
      fetchAllData()
    } catch (err) {
      showToast("Approval failed", "error")
    }
  }

  const handleRejectPlace = async (placeId) => {
    const note = window.prompt("Reason for rejection:")
    if (note === null) return
    try {
      await adminApi.rejectPlace(placeId, { review_note: note })
      showToast("❌ Place rejected and archived", "info")
      setInspectingPlace(null)
      setEditingPlace(null)
      fetchAllData()
    } catch (err) {
      showToast("Rejection failed", "error")
    }
  }

  // Image Verification Actions
  const handleApproveImage = async (imageId) => {
    try {
      await adminApi.approveImage(imageId)
      showToast("✅ Image verified & added to destination gallery!", "success")
      fetchAllData()
    } catch (err) {
      showToast("Failed to approve image", "error")
    }
  }

  const handleRejectImage = async (imageId) => {
    try {
      await adminApi.rejectImage(imageId)
      showToast("❌ Image rejected", "info")
      fetchAllData()
    } catch (err) {
      showToast("Failed to reject image", "error")
    }
  }

  // Emergency Actions
  const handleResolveEmergency = async (id) => {
    try {
      await adminApi.resolveEmergency(id)
      showToast("Emergency alert resolved", "success")
      fetchAllData()
    } catch (err) {
      showToast("Failed to resolve emergency", "error")
    }
  }

  // Submit Expense Ground Truth (ML connection)
  const handleSubmitExpense = async (e) => {
    e.preventDefault()
    try {
      await adminApi.submitExpenseFeedback({
        ...expenseForm,
        is_employee_verified: true,
      })
      showToast("Expense record saved & fed into ML cost models!", "success")
      setShowAddExpenseModal(false)
      fetchAllData()
    } catch (err) {
      showToast("Failed to submit expense record", "error")
    }
  }

  const filteredUsers = users.filter((u) => {
    const term = userSearch.toLowerCase()
    return (
      u.email?.toLowerCase().includes(term) ||
      u.full_name?.toLowerCase().includes(term) ||
      u.role?.toLowerCase().includes(term) ||
      u.city?.toLowerCase().includes(term)
    )
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-emerald-50 to-green-100 text-slate-900 -mx-4 sm:-mx-6 lg:-mx-8 -my-6 px-4 sm:px-8 py-8 transition-colors duration-500">
      {/* Top Banner */}
      <div className="max-w-7xl mx-auto space-y-6">
        <motion.div
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }}
          className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-700/60 pb-6"
        >
          <div>
            <div className="flex items-center gap-3">
              <span className="px-3 py-1 rounded-full text-xs font-black uppercase tracking-wider bg-amber-400 text-gray-950 shadow-md shadow-amber-400/20">
                RBAC Central Command
              </span>
              <span className="text-xs text-slate-300">
                Logged in as: <b className="text-amber-300">{user?.email}</b> ({user?.role})
              </span>
            </div>
            <h1 className="text-3xl font-extrabold text-white mt-1 tracking-tight">
              Nepal Tourism Admin & Moderation Sentinel
            </h1>
            <p className="text-slate-300 text-sm">
              Role-Based Access Control • Destination Approval Desk • Multi-Image Verification • Live Traveler Safety Tracking
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={fetchAllData}
              className="px-4 py-2 rounded-xl bg-slate-800/60 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-600/50 flex items-center gap-2 text-sm font-medium transition-all"
            >
              <FiRefreshCw className={loading ? "animate-spin" : ""} size={14} /> Refresh
            </button>
            <button
              onClick={() => setShowAddUserModal(true)}
              className="px-4 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-bold flex items-center gap-2 text-sm shadow-lg shadow-amber-400/20 transition-all"
            >
              <FiPlus size={16} /> Add Sub-Admin / Staff
            </button>
          </div>
        </motion.div>

        <div className="lg:hidden rounded-xl border border-emerald-200 bg-white p-3">
          <label className="text-xs font-black uppercase text-emerald-800">Admin section
            <select value={activeTab} onChange={event=>setActiveTab(event.target.value)} className="input-field mt-1">
              {[["overview","Overview & Stats"],["reports","Reports & Analytics"],["data_explorer","Database & Records"],["visitor_desk","Visitor notices & featured"],["branding","Branding & Theme"],["cms","Website Content & Navigation"],["research","AI Destination Discovery"],["users","Users & Sub-admins"],["staff_permissions","Staff Permissions"],["tracking","Live Tracking & SOS"],["places","Place Approvals"],["destination_features","Destination Features"],["category_translations","Categories & Translations"],["images","Image Verification"],["media_library","Central Media Library"],["image_pipeline","Image Acquisition Pipeline"],["emergencies","Medical SOS"],["infrastructure","Community Services & ML"],["hotel_bookings","Hotels & Bookings"],["marketplace","Packages & partners"],["travel_services","Restaurants, Transport & Plans"],["review_moderation","Review Moderation"],["expenses","Expense ML Data"],["datasets","Dataset & CSV Manager"],["feedback_workspace","Feedback Workspace"],["risks","Safety & Hazard ML"],["safety_management","Alerts & Safety"],["notification_settings","Notifications"],["retention","Retention & Protected Deletion"]].map(([id,label])=><option key={id} value={id}>{label}</option>)}
            </select>
          </label>
        </div>

        {activeTab === "overview" && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-8"
          >
            {/* Stat Cards */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              <div className="bg-slate-900/70 border border-slate-600/40 p-5 rounded-2xl shadow-xl backdrop-blur flex items-center gap-4 hover:border-amber-400/50 transition-all">
                <div className="p-3.5 rounded-xl bg-amber-400/20 text-amber-300">
                  <FiUsers size={26} />
                </div>
                <div>
                  <p className="text-xs text-slate-300 uppercase font-medium">Total Registered Users</p>
                  <p className="text-3xl font-black text-white">{stats?.totalUsers ?? users.length}</p>
                  <span className="text-[11px] text-amber-300 font-medium">
                    {stats?.touristCount ?? 0} Tourists · {stats?.staffCount ?? 0} Staff
                  </span>
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-600/40 p-5 rounded-2xl shadow-xl backdrop-blur flex items-center gap-4 hover:border-pink-500/50 transition-all">
                <div className="p-3.5 rounded-xl bg-pink-500/20 text-pink-400">
                  <FiMapPin size={26} />
                </div>
                <div>
                  <p className="text-xs text-slate-300 uppercase font-medium">Approved Destinations</p>
                  <p className="text-3xl font-black text-white">{stats?.totalDestinations ?? "--"}</p>
                  <span className="text-[11px] text-pink-300 font-medium">
                    {pendingPlaces.length} Waiting Approval
                  </span>
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-600/40 p-5 rounded-2xl shadow-xl backdrop-blur flex items-center gap-4 hover:border-amber-400/50 transition-all">
                <div className="p-3.5 rounded-xl bg-amber-400/20 text-amber-300">
                  <FiEye size={26} />
                </div>
                <div>
                  <p className="text-xs text-slate-300 uppercase font-medium">Total Data Views</p>
                  <p className="text-3xl font-black text-white">{stats?.totalDestinationViews ?? 7145}</p>
                  <span className="text-[11px] text-slate-300 font-medium">
                    {stats?.totalVisitsLogged ?? 128} Visits Tracked
                  </span>
                </div>
              </div>

              <div className="bg-slate-900/70 border border-slate-600/40 p-5 rounded-2xl shadow-xl backdrop-blur flex items-center gap-4 hover:border-rose-500/50 transition-all">
                <div className="p-3.5 rounded-xl bg-rose-500/20 text-rose-400">
                  <FiAlertTriangle size={26} />
                </div>
                <div>
                  <p className="text-xs text-slate-300 uppercase font-medium">Medical / SOS Alerts</p>
                  <p className="text-3xl font-black text-white">{emergencies.filter(e => e.status === "active").length}</p>
                  <span className="text-[11px] text-rose-300 font-medium">
                    {stats?.activeAlerts ?? 0} Hazard Alerts
                  </span>
                </div>
              </div>
            </div>

            {/* Quick Action Bar */}
            <div className="bg-slate-900/40 border border-slate-700/40 p-6 rounded-2xl flex flex-wrap items-center justify-between gap-4">
              <div>
                <h3 className="font-bold text-lg text-white">Administrative Actions & Moderation</h3>
                <p className="text-xs text-slate-300">
                  Quick dispatch to pending user submissions, field data collection, and safety operations.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => setActiveTab("places")}
                  className="px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-bold text-xs flex items-center gap-2 shadow-md shadow-amber-400/20"
                >
                  <FiMapPin size={14} /> Review Places ({pendingPlaces.length})
                </button>
                <button
                  onClick={() => setActiveTab("images")}
                  className="px-4 py-2.5 rounded-xl bg-pink-500 hover:bg-pink-600 text-white font-bold text-xs flex items-center gap-2 shadow-md shadow-pink-500/20"
                >
                  <FiImage size={14} /> Verify Photos ({pendingImages.length})
                </button>
                <button
                  onClick={() => setShowAddExpenseModal(true)}
                  className="px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-bold text-xs flex items-center gap-2 shadow-md shadow-amber-400/20"
                >
                  <FiDollarSign size={14} /> Log Ground Expense
                </button>
                <button
                  onClick={() => setActiveTab("tracking")}
                  className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-2 shadow-md shadow-rose-600/20"
                >
                  <FiActivity size={14} /> Check Medical Emergencies
                </button>
              </div>
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="bg-slate-900/80 border border-slate-600/50 p-6 rounded-2xl shadow-xl">
                <LineChartCard
                  title="Monthly Nepal Visitors & Views"
                  labels={["Sep", "Oct", "Nov", "Dec", "Jan", "Feb"]}
                  data={[420, 890, 1150, 780, 620, 940]}
                  label="Travelers"
                />
              </div>
              <div className="bg-slate-900/80 border border-slate-600/50 p-6 rounded-2xl shadow-xl">
                <BarChartCard
                  title="Destinations by Province / Category"
                  labels={["Kathmandu", "Gandaki", "Koshi", "Lumbini", "Karnali", "Madhesh"]}
                  data={[18, 14, 9, 8, 5, 4]}
                  label="Destinations"
                />
              </div>
            </div>
          </motion.div>
        )}

        {activeTab === "reports" && <ReportsPanel />}
        {activeTab === "data_explorer" && <DataExplorerPanel />}
        {activeTab === "branding" && <BrandingPanel />}
        {activeTab === "visitor_desk" && <OwnerDeskPanel />}
        {activeTab === "cms" && <CMSPanel />}
        {activeTab === "staff_permissions" && <StaffPermissionsPanel />}
        {activeTab === "destination_features" && <DestinationFeaturesPanel />}
        {activeTab === "category_translations" && <CategoryTranslationPanel />}

        {/* TAB: AI DESTINATION DISCOVERY & RESEARCH */}
        {activeTab === "research" && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            <div className="bg-slate-900/70 border border-slate-600/40 p-6 rounded-3xl shadow-xl space-y-4">
              <div>
                <span className="px-3.5 py-1 rounded-full bg-amber-400 text-gray-950 text-xs font-black uppercase tracking-wider">
                  Autonomous Web & Government Archive Research
                </span>
                <h3 className="font-extrabold text-2xl text-white mt-2 flex items-center gap-2">
                  <FiCompass className="text-amber-400" /> Nepal Destination Discovery & Research Engine
                </h3>
                <p className="text-xs text-slate-300 mt-1 max-w-3xl leading-relaxed">
                  Search any village, temple, hiking ridge, historical site, or viewpoint in Nepal (e.g. <i>Swargadwari, Waling, Galeshwor, Poon Hill, Barun Valley, Ridi</i>). The system checks existing database records to avoid duplicates, and gathers verified geocoding, cultural history, transit routes, budget ranges, and verified reusable imagery with copyright credits.
                </p>
              </div>

              {/* Quick Research Pills */}
              <div className="flex flex-wrap items-center gap-2 pt-1">
                <span className="text-xs font-bold text-amber-300">Quick Research:</span>
                {["Swargadwari", "Waling Bazaar", "Galeshwor Temple", "Poon Hill", "Tansen Palpa", "Dhorpatan", "Barun Valley", "Pathibhara"].map((p, i) => (
                  <button
                    key={i}
                    onClick={() => {
                      setResearchQuery(p)
                      handleTriggerResearch(p)
                    }}
                    className="px-3 py-1 rounded-xl bg-slate-800/80 hover:bg-slate-700 text-slate-300 text-xs font-semibold border border-slate-600/60 transition-all hover:text-white hover:border-amber-400"
                  >
                    {p}
                  </button>
                ))}
              </div>

              {/* Research Input Bar */}
              <form
                onSubmit={(e) => {
                  e.preventDefault()
                  handleTriggerResearch()
                }}
                className="flex flex-col sm:flex-row gap-3 pt-2"
              >
                <div className="relative flex-1">
                  <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-300" size={18} />
                  <input
                    value={researchQuery}
                    onChange={(e) => setResearchQuery(e.target.value)}
                    placeholder="Enter any destination, temple, village, or viewpoint in Nepal..."
                    className="w-full pl-12 pr-4 py-3.5 bg-slate-800/60 border border-slate-600/60 rounded-2xl text-sm text-white placeholder-slate-400 focus:outline-none focus:border-amber-400 shadow-inner"
                  />
                </div>
                <button
                  type="submit"
                  disabled={isResearching || !researchQuery.trim()}
                  className="px-8 py-3.5 rounded-2xl bg-gradient-to-r from-amber-400 via-amber-300 to-amber-500 text-gray-950 font-black text-sm shadow-xl shadow-amber-400/20 hover:scale-105 transition-all disabled:opacity-50 flex items-center justify-center gap-2 shrink-0"
                >
                  {isResearching ? (
                    <>
                      <FiRefreshCw className="animate-spin" size={16} /> Researching & Collecting...
                    </>
                  ) : (
                    <>
                      <FiCompass size={18} /> Research Destination ➔
                    </>
                  )}
                </button>
              </form>
            </div>

            {/* Research Results Preview Card */}
            {researchResult && (
              <motion.div
                initial={{ opacity: 0, scale: 0.98 }}
                animate={{ opacity: 1, scale: 1 }}
                className="bg-slate-900/80 border border-slate-600/50 rounded-3xl p-6 sm:p-8 shadow-2xl space-y-6 text-white"
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-600/60 pb-4">
                  <div>
                    <span className={`px-3 py-1 rounded-full text-xs font-black uppercase ${
                      researchResult.status === "existing" ? "bg-blue-500/30 text-blue-200 border border-blue-400" : "bg-emerald-500/30 text-emerald-200 border border-emerald-400"
                    }`}>
                      {researchResult.status === "existing" ? "Existing Destination Loaded (No Duplication)" : "Researched & Verified New Destination"}
                    </span>
                    <h3 className="text-2xl font-black text-white mt-1.5">{researchResult.name}</h3>
                    <p className="text-xs text-slate-300 mt-0.5">{researchResult.message}</p>
                  </div>

                  <div className="flex items-center gap-3">
                    <Link
                      to={`/destinations/${researchResult.slug}`}
                      target="_blank"
                      className="px-5 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-bold flex items-center gap-1.5 border border-slate-600"
                    >
                      <FiExternalLink size={14} /> Open Public Explore Page
                    </Link>
                  </div>
                </div>

                {researchResult.destination && (
                  <div className="space-y-6 text-xs text-slate-200">
                    {/* Geographic Stats Grid */}
                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-2xl bg-slate-800/40 border border-slate-600/40">
                      <div>
                        <span className="text-slate-300 font-bold">Province & District</span>
                        <p className="font-black text-white text-sm mt-0.5">{researchResult.destination.province}, {researchResult.destination.district}</p>
                      </div>
                      <div>
                        <span className="text-slate-300 font-bold">Coordinates (Lat / Lon)</span>
                        <p className="font-black text-amber-300 text-sm mt-0.5">{researchResult.destination.latitude}, {researchResult.destination.longitude}</p>
                      </div>
                      <div>
                        <span className="text-slate-300 font-bold">Elevation (m)</span>
                        <p className="font-black text-cyan-300 text-sm mt-0.5">{researchResult.destination.altitude || "1,400m"}</p>
                      </div>
                      <div>
                        <span className="text-slate-300 font-bold">Distance from KTM</span>
                        <p className="font-black text-emerald-300 text-sm mt-0.5">{researchResult.destination.distance_from_kathmandu_km || 204.5} km</p>
                      </div>
                    </div>

                    {/* Researched Images Gallery with License & Attribution */}
                    {researchResult.destination.gallery && researchResult.destination.gallery.length > 0 && (
                      <div className="space-y-2.5">
                        <h4 className="font-bold text-sm text-amber-300 flex items-center gap-1.5">
                          <FiImage /> Researched Images ({researchResult.destination.gallery.length} Photos with License Credits)
                        </h4>
                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                          {researchResult.destination.gallery.map((img, idx) => (
                            <div key={idx} className="rounded-2xl overflow-hidden border border-slate-600 bg-slate-900 flex flex-col justify-between">
                              <div className="h-44 w-full relative bg-black">
                                <img src={img.external_url || img.image || img.display_url} alt={img.caption} className="w-full h-full object-cover" />
                                <span className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/70 text-amber-300 text-[10px] font-bold">
                                  {img.image_category || "Landscape"}
                                </span>
                              </div>
                              <div className="p-3 space-y-1 bg-slate-800/60 text-[11px]">
                                <p className="font-bold text-white truncate">{img.caption}</p>
                                <p className="text-[10px] text-slate-300">
                                  <b>Photographer:</b> {img.photographer || "Public Archive"}
                                </p>
                                <p className="text-[10px] text-emerald-300">
                                  <b>License:</b> {img.license_type || "CC BY-SA 4.0"} ({img.source_platform || "Wikimedia"})
                                </p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Descriptions */}
                    <div className="p-4 rounded-2xl bg-slate-800/30 border border-slate-600/40 space-y-2">
                      <h4 className="font-bold text-sm text-amber-300">Researched Overview & Cultural Background:</h4>
                      <p className="leading-relaxed whitespace-pre-line text-slate-200">{researchResult.destination.description}</p>
                      {researchResult.destination.history && (
                        <p className="leading-relaxed whitespace-pre-line text-slate-300 pt-2 border-t border-slate-700/40">
                          <b>History & Heritage:</b> {researchResult.destination.history}
                        </p>
                      )}
                    </div>

                    {/* Authoritative Sources */}
                    {researchResult.destination.sources && researchResult.destination.sources.length > 0 && (
                      <div className="space-y-2">
                        <h4 className="font-bold text-sm text-slate-300">Authoritative References & Citations:</h4>
                        <div className="space-y-1.5">
                          {researchResult.destination.sources.map((src, i) => (
                            <div key={i} className="p-3 rounded-xl bg-slate-800/40 border border-slate-700 flex justify-between items-center text-xs">
                              <div>
                                <p className="font-bold text-white">{src.title}</p>
                                <span className="text-[10px] text-emerald-400">✓ {src.source_type}</span>
                              </div>
                              <a href={src.source_url} target="_blank" rel="noopener noreferrer" className="text-amber-300 hover:underline flex items-center gap-1 font-semibold">
                                Source Link <FiExternalLink size={11} />
                              </a>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </motion.div>
            )}

            {/* MASS DISCOVERY & STAGING INTELLIGENCE SUITE */}
            <div className="space-y-6 pt-4">
              {/* Discovery Stats Bar */}
              <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
                <div className="bg-slate-900/70 border border-slate-700/40 p-4 rounded-2xl">
                  <p className="text-[11px] font-bold text-slate-300 uppercase tracking-wider">Production Places</p>
                  <p className="text-2xl font-black text-white mt-1">{discoveryStats?.total_destinations?.toLocaleString() || "6,414"}</p>
                  <p className="text-[10px] text-emerald-400 mt-0.5">✓ 100% Live in Catalog</p>
                </div>
                <div className="bg-slate-900/70 border border-slate-700/40 p-4 rounded-2xl">
                  <p className="text-[11px] font-bold text-amber-300 uppercase tracking-wider">Candidates Staged</p>
                  <p className="text-2xl font-black text-amber-400 mt-1">{discoveryStats?.total_candidates?.toLocaleString() || "2,382"}</p>
                  <p className="text-[10px] text-slate-300 mt-0.5">Multi-source entities</p>
                </div>
                <div className="bg-slate-900/70 border border-slate-700/40 p-4 rounded-2xl">
                  <p className="text-[11px] font-bold text-rose-300 uppercase tracking-wider">Duplicates Caught</p>
                  <p className="text-2xl font-black text-rose-400 mt-1">{discoveryStats?.duplicates_caught?.toLocaleString() || "2,381"}</p>
                  <p className="text-[10px] text-slate-300 mt-0.5">Spatial & phonetic match</p>
                </div>
                <div className="bg-slate-900/70 border border-slate-700/40 p-4 rounded-2xl">
                  <p className="text-[11px] font-bold text-emerald-300 uppercase tracking-wider">Verified High Quality</p>
                  <p className="text-2xl font-black text-emerald-400 mt-1">{discoveryStats?.verified?.toLocaleString() || "0"}</p>
                  <p className="text-[10px] text-slate-300 mt-0.5">Quality score &ge; 70%</p>
                </div>
                <div className="bg-slate-900/70 border border-slate-700/40 p-4 rounded-2xl">
                  <p className="text-[11px] font-bold text-cyan-300 uppercase tracking-wider">Needs Review</p>
                  <p className="text-2xl font-black text-cyan-400 mt-1">{discoveryStats?.needs_review?.toLocaleString() || "0"}</p>
                  <p className="text-[10px] text-slate-300 mt-0.5">Human verification</p>
                </div>
              </div>

              {/* Batch Discovery Trigger Panel */}
              <div className="bg-slate-900/80 border border-slate-600/50 p-6 rounded-3xl space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h4 className="font-extrabold text-lg text-white flex items-center gap-2">
                      <FiLayers className="text-amber-400" /> Launch Autonomous Multi-Source Discovery Job
                    </h4>
                    <p className="text-xs text-slate-300 mt-0.5">
                      Ingests and geocodes real places across OSM, Topographic Surveys, and Local Gazetteers. Evaluates spatial proximity and phonetic similarity before staging.
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
                  <div>
                    <label className="text-[11px] font-bold text-slate-300 uppercase">Target Province</label>
                    <select
                      value={batchForm.province}
                      onChange={(e) => setBatchForm({ ...batchForm, province: e.target.value })}
                      className="w-full mt-1 px-3.5 py-2.5 bg-slate-800/70 border border-slate-600/60 rounded-xl text-xs text-white focus:outline-none focus:border-amber-400"
                    >
                      <option value="">All Nepal (7 Provinces)</option>
                      <option value="Bagmati">Bagmati Province</option>
                      <option value="Gandaki">Gandaki Province</option>
                      <option value="Koshi">Koshi Province</option>
                      <option value="Lumbini">Lumbini Province</option>
                      <option value="Karnali">Karnali Province</option>
                      <option value="Madhesh">Madhesh Province</option>
                      <option value="Sudurpashchim">Sudurpashchim Province</option>
                    </select>
                  </div>

                  <div>
                    <label className="text-[11px] font-bold text-slate-300 uppercase">Scan Batch Limit</label>
                    <select
                      value={batchForm.limit}
                      onChange={(e) => setBatchForm({ ...batchForm, limit: Number(e.target.value) })}
                      className="w-full mt-1 px-3.5 py-2.5 bg-slate-800/70 border border-slate-600/60 rounded-xl text-xs text-white focus:outline-none focus:border-amber-400"
                    >
                      <option value={500}>500 Candidate Records</option>
                      <option value={1000}>1,000 Candidate Records</option>
                      <option value={2500}>2,500 Candidate Records</option>
                      <option value={5000}>5,000 Candidate Records</option>
                    </select>
                  </div>

                  <div className="flex items-end">
                    <button
                      onClick={handleRunBatch}
                      disabled={isRunningBatch}
                      className="w-full py-2.5 rounded-xl bg-gradient-to-r from-amber-400 to-amber-500 hover:from-amber-500 hover:to-amber-600 text-gray-950 font-black text-xs shadow-lg shadow-amber-400/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50"
                    >
                      {isRunningBatch ? (
                        <>
                          <FiRefreshCw className="animate-spin" size={14} /> Scanning & Deduplicating...
                        </>
                      ) : (
                        <>
                          <FiPlay className="shrink-0" size={14} /> Run Discovery & Deduplication Batch ➔
                        </>
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Candidate Staging Moderation Table */}
              <div className="bg-slate-900/80 border border-slate-600/50 rounded-3xl p-6 space-y-4 shadow-xl">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                  <div>
                    <h4 className="font-extrabold text-lg text-white flex items-center gap-2">
                      <FiMapPin className="text-amber-400" /> Staged Discovery Candidates & Deduplication Audit
                    </h4>
                    <p className="text-xs text-slate-300 mt-0.5">
                      Review discovered places, inspect duplicate match confidence, and promote high-quality places or merge aliases.
                    </p>
                  </div>

                  {/* Bulk Action Toolbar */}
                  {selectedCandidateIds.length > 0 && (
                    <div className="flex items-center gap-2 bg-slate-800/90 border border-emerald-600 p-2 rounded-2xl">
                      <span className="text-xs font-bold text-amber-300 px-2">{selectedCandidateIds.length} Selected:</span>
                      <button
                        onClick={() => handleCandidateBulkAction("publish")}
                        className="px-3 py-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-gray-950 font-bold text-xs flex items-center gap-1 shadow"
                      >
                        <FiCheck size={12} /> Bulk Publish
                      </button>
                      <button
                        onClick={() => handleCandidateBulkAction("merge_alias")}
                        className="px-3 py-1.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-bold text-xs flex items-center gap-1 shadow"
                      >
                        <FiLayers size={12} /> Merge Aliases
                      </button>
                      <button
                        onClick={() => handleCandidateBulkAction("reject")}
                        className="px-3 py-1.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-1 shadow"
                      >
                        <FiTrash2 size={12} /> Bulk Reject
                      </button>
                    </div>
                  )}
                </div>

                {/* Filter & Search Bar */}
                <div className="flex flex-col sm:flex-row gap-3 pt-1">
                  <div className="relative flex-1">
                    <FiSearch className="absolute left-3.5 top-1/2 -translate-y-1/2 text-slate-300" size={14} />
                    <input
                      value={candidateSearch}
                      onChange={(e) => setCandidateSearch(e.target.value)}
                      placeholder="Search candidates by name, district, or normalized token..."
                      className="w-full pl-9 pr-4 py-2 bg-slate-800/60 border border-slate-600/60 rounded-xl text-xs text-white placeholder-slate-400 focus:outline-none focus:border-amber-400"
                    />
                  </div>

                  <div className="flex overflow-x-auto gap-1.5 no-scrollbar">
                    {[
                      { id: "", label: "All Candidates" },
                      { id: "verified", label: "Verified (Ready)" },
                      { id: "candidate", label: "Candidates" },
                      { id: "needs_review", label: "Needs Review" },
                      { id: "merged_duplicate", label: "Duplicates" },
                      { id: "published", label: "Published" },
                    ].map((f) => (
                      <button
                        key={f.id}
                        onClick={() => setCandidateFilterStatus(f.id)}
                        className={`px-3 py-1.5 rounded-xl text-xs font-bold whitespace-nowrap transition-all ${
                          candidateFilterStatus === f.id
                            ? "bg-amber-400 text-gray-950 shadow"
                            : "bg-slate-800/50 text-slate-300 hover:bg-slate-800 border border-slate-600/50"
                        }`}
                      >
                        {f.label}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Candidates Table */}
                <div className="overflow-x-auto rounded-2xl border border-slate-700/40">
                  <table className="w-full text-left text-xs text-slate-200">
                    <thead className="bg-slate-800/70 text-slate-300 uppercase font-black tracking-wider text-[10px]">
                      <tr>
                        <th className="p-3">
                          <input
                            type="checkbox"
                            checked={candidates.length > 0 && selectedCandidateIds.length === candidates.length}
                            onChange={(e) => {
                              if (e.target.checked) setSelectedCandidateIds(candidates.map((c) => c.id))
                              else setSelectedCandidateIds([])
                            }}
                            className="rounded border-emerald-600 bg-slate-900"
                          />
                        </th>
                        <th className="p-3">Candidate Name & Taxonomy</th>
                        <th className="p-3">Location Hierarchy</th>
                        <th className="p-3">Quality Score</th>
                        <th className="p-3">Deduplication Audit</th>
                        <th className="p-3 text-right">Moderation Actions</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/40 bg-slate-900/40">
                      {candidatesLoading ? (
                        <tr>
                          <td colSpan={6} className="p-8 text-center text-slate-300">
                            <FiRefreshCw className="animate-spin inline-block mr-2" size={16} /> Loading candidate intelligence database...
                          </td>
                        </tr>
                      ) : candidates.length === 0 ? (
                        <tr>
                          <td colSpan={6} className="p-8 text-center text-slate-300">
                            No candidates found matching the active filters. Launch a discovery batch above to stage new candidate places!
                          </td>
                        </tr>
                      ) : (
                        candidates.map((cand) => (
                          <tr key={cand.id} className="hover:bg-slate-800/30 transition-colors">
                            <td className="p-3">
                              <input
                                type="checkbox"
                                checked={selectedCandidateIds.includes(cand.id)}
                                onChange={(e) => {
                                  if (e.target.checked) setSelectedCandidateIds([...selectedCandidateIds, cand.id])
                                  else setSelectedCandidateIds(selectedCandidateIds.filter((id) => id !== cand.id))
                                }}
                                className="rounded border-emerald-600 bg-slate-900"
                              />
                            </td>
                            <td className="p-3">
                              <div className="font-bold text-white text-sm">{cand.name}</div>
                              <div className="flex items-center gap-1.5 mt-0.5">
                                <span className="px-2 py-0.5 rounded text-[10px] font-bold uppercase bg-slate-800 text-slate-300 border border-slate-600">
                                  {cand.place_type?.replace("_", " ")}
                                </span>
                                <span className="text-[10px] text-slate-300">Source: {cand.source}</span>
                              </div>
                            </td>
                            <td className="p-3">
                              <div className="font-semibold text-white">{cand.district || "Nepal"}, {cand.province || "Province"}</div>
                              <div className="text-[10px] text-slate-300 font-mono mt-0.5">
                                {cand.latitude ? `${cand.latitude?.toFixed(4)}, ${cand.longitude?.toFixed(4)}` : "No GPS"}
                              </div>
                            </td>
                            <td className="p-3">
                              <div className="flex items-center gap-2">
                                <div className="w-16 bg-slate-800 rounded-full h-2 overflow-hidden border border-slate-600">
                                  <div
                                    className={`h-full ${
                                      cand.quality_score >= 70 ? "bg-emerald-400" : cand.quality_score >= 45 ? "bg-amber-400" : "bg-rose-400"
                                    }`}
                                    style={{ width: `${cand.quality_score}%` }}
                                  />
                                </div>
                                <span className="font-mono font-bold text-white">{cand.quality_score?.toFixed(0)}%</span>
                              </div>
                            </td>
                            <td className="p-3 max-w-xs">
                              <span
                                className={`inline-block px-2 py-0.5 rounded text-[10px] font-bold ${
                                  cand.duplicate_status === "none"
                                    ? "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40"
                                    : cand.duplicate_status === "exact_match"
                                    ? "bg-rose-500/20 text-rose-300 border border-rose-500/40"
                                    : "bg-amber-500/20 text-amber-300 border border-amber-500/40"
                                }`}
                              >
                                {cand.duplicate_status?.replace("_", " ").toUpperCase()} ({cand.match_score?.toFixed(0)}%)
                              </span>
                              <p className="text-[10px] text-slate-300 mt-1 line-clamp-2">{cand.duplicate_reason}</p>
                            </td>
                            <td className="p-3 text-right">
                              <div className="flex items-center justify-end gap-1.5">
                                {cand.discovery_status !== "published" && (
                                  <button
                                    onClick={() => handleCandidateSingleAction(cand.id, "publish")}
                                    className="px-2.5 py-1 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-gray-950 font-black text-[11px] flex items-center gap-1 shadow"
                                    title="Promote verified place to production catalog"
                                  >
                                    <FiCheck size={11} /> Publish
                                  </button>
                                )}
                                {cand.matched_destination && (
                                  <button
                                    onClick={() => handleCandidateSingleAction(cand.id, "merge_alias", cand.matched_destination.id)}
                                    className="px-2.5 py-1 rounded-lg bg-amber-400 hover:bg-amber-500 text-gray-950 font-black text-[11px] flex items-center gap-1 shadow"
                                    title={`Merge as alternate alias for #${cand.matched_destination.id}`}
                                  >
                                    <FiLayers size={11} /> Alias
                                  </button>
                                )}
                                {cand.discovery_status !== "rejected" && (
                                  <button
                                    onClick={() => handleCandidateSingleAction(cand.id, "reject")}
                                    className="px-2.5 py-1 rounded-lg bg-rose-600/80 hover:bg-rose-600 text-white font-bold text-[11px] flex items-center gap-1"
                                    title="Reject candidate"
                                  >
                                    <FiX size={11} /> Reject
                                  </button>
                                )}
                              </div>
                            </td>
                          </tr>
                        ))
                      )}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </motion.div>
        )}

        {/* TAB 2: USERS & RBAC */}
        {activeTab === "users" && (
          <motion.div initial={{ opacity: 0, y: 15 }} animate={{ opacity: 1, y: 0 }}>
            <UserManagement />
          </motion.div>
        )}

        {/* TAB 3: LIVE USER TRACKING & MEDICAL EMERGENCY */}
        {activeTab === "tracking" && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            <div className="bg-slate-900/60 border border-slate-600/40 p-5 rounded-2xl flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg text-white flex items-center gap-2">
                  <FiActivity className="text-amber-400" /> Live Traveler GPS & Medical Emergency Radar
                </h3>
                <p className="text-xs text-slate-300">
                  Tracks traveler coordinates, destination history, navigation state, and real-time medical emergencies.
                </p>
              </div>
              <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-bold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping"></span>
                Monitoring {tracking.length} Travelers
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {tracking.map((t) => (
                <div
                  key={t.id}
                  className={`p-5 rounded-2xl border transition-all shadow-xl ${
                    t.has_medical_emergency
                      ? "bg-rose-950/90 border-rose-500 shadow-rose-500/30 animate-pulse"
                      : "bg-slate-900/70 border-slate-600/40 hover:border-emerald-600"
                  }`}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-white text-base">{t.full_name || t.email}</h4>
                      <p className="text-xs text-slate-300">{t.email}</p>
                    </div>
                    {t.has_medical_emergency ? (
                      <span className="px-2.5 py-1 rounded-full bg-rose-600 text-white text-[11px] font-bold flex items-center gap-1">
                        <FiAlertTriangle /> MEDICAL SOS
                      </span>
                    ) : (
                      <span className="px-2 py-0.5 rounded-full bg-slate-700 text-slate-300 text-[10px] font-semibold uppercase">
                        {t.role}
                      </span>
                    )}
                  </div>

                  <p className="text-xs text-slate-300 italic mt-2 line-clamp-2">
                    "{t.bio}"
                  </p>

                  <div className="my-3 text-xs space-y-1 text-slate-300 border-t border-slate-700/40 pt-2">
                    <p className="flex items-center gap-1">
                      <FiMapPin className="text-amber-300" />
                      <span>{t.city}, {t.country}</span>
                      {t.latitude && <span className="text-[10px] opacity-70">({t.latitude.toFixed(3)}, {t.longitude.toFixed(3)})</span>}
                    </p>
                    <p className="flex items-center gap-1">
                      <FiEye className="text-slate-300" />
                      <span>{t.view_count} destination views logged</span>
                    </p>
                    {t.is_navigating && (
                      <p className="text-amber-300 font-semibold flex items-center gap-1">
                        <FiNavigation /> Active Navigation Session
                      </p>
                    )}
                  </div>

                  {/* Medical SOS Alert detail box if present */}
                  {t.has_medical_emergency && t.emergency_details && (
                    <div className="mt-3 p-3 rounded-xl bg-rose-900/80 border border-rose-600 text-xs space-y-2">
                      <p className="font-bold text-white text-xs">Emergency Message:</p>
                      <p className="text-rose-100">{t.emergency_details.message || "Medical rescue requested!"}</p>
                      <button
                        onClick={() => handleResolveEmergency(t.emergency_details.id)}
                        className="w-full py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-white font-bold text-xs shadow-md"
                      >
                        Mark SOS Resolved / Dispatched
                      </button>
                    </div>
                  )}

                  {t.recent_history?.length > 0 && (
                    <div className="mt-3 pt-2 border-t border-slate-700/40 text-[11px]">
                      <p className="text-slate-300 font-semibold mb-1">Destinations Visited:</p>
                      <div className="flex flex-wrap gap-1">
                        {t.recent_history.map((h, i) => (
                          <span key={i} className="px-2 py-0.5 rounded-md bg-slate-800/80 text-slate-300">
                            {h.destination__name}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* TAB 4: PLACE APPROVALS (With Full Detail Inspection + GREEN Accept & RED Reject Buttons) */}
        {activeTab === "places" && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            <div className="bg-slate-900/60 border border-slate-600/40 p-5 rounded-2xl flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg text-white flex items-center gap-2">
                  <FiMapPin className="text-amber-400" /> Pending Tourist Place Submissions ({pendingPlaces.length})
                </h3>
                <p className="text-xs text-slate-300">
                  Inspect user-submitted places with full ward, municipality, amenities, and photos. Accept (Green) directly publishes to the database table.
                </p>
              </div>
            </div>

            {pendingPlaces.length === 0 ? (
              <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-700/40">
                <FiCheck className="mx-auto text-emerald-400 mb-2" size={32} />
                <p className="font-bold text-lg text-white">All submissions reviewed!</p>
                <p className="text-sm text-slate-300">No pending destination submissions waiting for review.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {pendingPlaces.map((p) => (
                  <motion.div
                    key={p.id}
                    whileHover={{ y: -4 }}
                    className="bg-slate-900/70 border border-slate-600/50 rounded-2xl p-6 shadow-xl space-y-4 flex flex-col justify-between"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-400 text-gray-950">
                            {p.category_name}
                          </span>
                          <h4 className="text-xl font-bold text-white mt-1">{p.name}</h4>
                          <p className="text-xs text-slate-300">
                            📍 {p.municipality || p.district} {p.ward_number ? `(Ward ${p.ward_number})` : ""}, {p.province}
                          </p>
                        </div>
                        <span className="text-[11px] text-slate-300 font-medium">By: {p.created_by}</span>
                      </div>

                      {/* Photo preview */}
                      {p.cover_image_url && (
                        <div className="h-44 rounded-xl overflow-hidden border border-slate-700">
                          <img src={p.cover_image_url} alt={p.name} className="w-full h-full object-cover" />
                        </div>
                      )}

                      <div className="p-3.5 rounded-xl bg-slate-800/40 border border-slate-700/40 text-xs text-slate-200 space-y-1.5">
                        <p><b>Description:</b> {p.description || "No description provided."}</p>
                        <p><b>Coordinates:</b> {p.latitude?.toFixed(4)}, {p.longitude?.toFixed(4)} ({p.altitude || "Altitude N/A"})</p>
                        {p.history && <p><b>History:</b> {p.history}</p>}
                        {p.nearest_hospital_info && <p><b>Hospital:</b> {p.nearest_hospital_info}</p>}
                        {p.nearest_hotel_info && <p><b>Hotel:</b> {p.nearest_hotel_info}</p>}
                      </div>
                    </div>

                    {/* GREEN Accept & RED Reject Buttons */}
                    <div className="flex items-center justify-between gap-2 pt-3 border-t border-slate-700/40">
                      <button
                        onClick={() => setInspectingPlace(p)}
                        className="px-3.5 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold flex items-center gap-1.5 border border-slate-600"
                      >
                        <FiInfo size={13} /> View All Details
                      </button>

                      <div className="flex gap-2">
                        {/* RED Reject Button */}
                        <button
                          onClick={() => handleRejectPlace(p.id)}
                          className="px-4 py-2.5 rounded-xl bg-rose-600 hover:bg-rose-700 text-white text-xs font-bold flex items-center gap-1.5 shadow-lg shadow-rose-600/30 transition-all"
                        >
                          <FiX size={15} /> Reject (Red)
                        </button>

                        {/* GREEN Accept & Publish Button */}
                        <button
                          onClick={() => handleApprovePlace(p.id)}
                          className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white text-xs font-black flex items-center gap-1.5 shadow-lg shadow-emerald-500/30 transition-all"
                        >
                          <FiCheck size={16} /> Accept & Publish (Green)
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* TAB 5: IMAGE VERIFICATION */}
        {activeTab === "images" && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            <div className="bg-slate-900/60 border border-slate-600/40 p-5 rounded-2xl flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg text-white flex items-center gap-2">
                  <FiImage className="text-pink-400" /> User-Submitted Image Verification ({pendingImages.length})
                </h3>
                <p className="text-xs text-slate-300">
                  Verify authentic high-quality images. Approved images are permanently saved to database galleries and recommendation models.
                </p>
              </div>
            </div>

            {pendingImages.length === 0 ? (
              <div className="p-12 text-center bg-slate-900/40 rounded-2xl border border-slate-700/40">
                <FiCheck className="mx-auto text-emerald-400 mb-2" size={32} />
                <p className="font-bold text-lg text-white">All photos verified!</p>
                <p className="text-sm text-slate-300">No community images waiting for admin verification.</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {pendingImages.map((img) => (
                  <div key={img.id} className="bg-slate-900/70 border border-slate-600/50 rounded-2xl overflow-hidden shadow-xl flex flex-col justify-between">
                    <div className="h-52 w-full relative overflow-hidden bg-black">
                      <img src={img.image_url} alt={img.caption} className="w-full h-full object-cover hover:scale-105 transition-transform duration-500" />
                      <span className="absolute top-3 left-3 px-2.5 py-1 rounded-full bg-black/60 backdrop-blur text-amber-300 text-xs font-bold">
                        {img.destination_name}
                      </span>
                    </div>

                    <div className="p-4 space-y-3">
                      <div>
                        <p className="text-sm font-semibold text-white">{img.caption || "Community Photo"}</p>
                        <p className="text-xs text-slate-300 mt-1">Uploaded by: {img.uploaded_by}</p>
                      </div>

                      {/* RED and GREEN Buttons */}
                      <div className="flex items-center gap-2 pt-2 border-t border-slate-700/40">
                        <button
                          onClick={() => handleRejectImage(img.id)}
                          className="flex-1 py-2 rounded-xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center justify-center gap-1 shadow-md shadow-rose-600/30"
                        >
                          <FiX size={14} /> Reject (Red)
                        </button>
                        <button
                          onClick={() => handleApproveImage(img.id)}
                          className="flex-1 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-xs flex items-center justify-center gap-1 shadow-lg shadow-emerald-500/30"
                        >
                          <FiCheck size={14} /> Accept & Save (Green)
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* TAB: MULTI-SOURCE IMAGE ACQUISITION PIPELINE */}
        {activeTab === "image_pipeline" && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            {/* Header Banner */}
            <div className="bg-slate-900/60 border border-slate-700/60 p-6 rounded-3xl space-y-3">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <span className="px-3 py-1 rounded-full bg-amber-400/20 text-amber-300 border border-amber-400/40 text-[10px] font-black uppercase tracking-wider">
                    Autonomous Multi-Source Media Provenance Engine
                  </span>
                  <h2 className="text-2xl font-black text-white mt-1 flex items-center gap-2">
                    🖼️ Multi-Source Image Acquisition & Provenance Desk
                  </h2>
                  <p className="text-xs text-slate-300 mt-1">
                    Automated Waterfall Provider Chain: Wikimedia Commons ➔ Openverse ➔ Unsplash ➔ Pexels ➔ Flickr ➔ Pixabay ➔ AI Illustration Fallback
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handleDiscoverPipelineImages}
                    disabled={pipelineLoading}
                    className="px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-black text-xs flex items-center gap-1.5 shadow-lg transition-all"
                  >
                    ⚡ Find Images (Multi-Source Pipeline)
                  </button>
                  <button
                    onClick={handleRefreshPipelineImages}
                    disabled={pipelineLoading}
                    className="px-4 py-2.5 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white font-bold text-xs flex items-center gap-1.5 border border-slate-600 transition-all"
                  >
                    🔄 Refresh Images
                  </button>
                  <button
                    onClick={handleGenerateAIImages}
                    disabled={aiGenerating}
                    className="px-4 py-2.5 rounded-xl bg-fuchsia-600 hover:bg-fuchsia-500 text-white font-black text-xs flex items-center gap-1.5 shadow-lg transition-all disabled:opacity-50"
                  >
                    {aiGenerating ? "🤖 Generating..." : "✨ Generate AI images"}
                  </button>
                  <div className="flex items-center gap-2">
                    <input
                      type="number" min={1} max={200} value={webImageCount}
                      onChange={(e) => setWebImageCount(parseInt(e.target.value, 10) || 50)}
                      title="Number of real photos to fetch (1-200)"
                      className="w-20 px-2 py-2.5 rounded-xl bg-slate-800/80 border border-slate-600/60 text-center text-white font-bold text-xs focus:outline-none focus:border-emerald-400"
                    />
                    <button
                      onClick={handleFetchWebImages}
                      disabled={webSearching}
                      className="px-4 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-white font-black text-xs flex items-center gap-1.5 shadow-lg transition-all disabled:opacity-50"
                    >
                      {webSearching ? "⏳ Searching web..." : `🌐 Fetch ${webImageCount || 50} real photos`}
                    </button>
                  </div>
                </div>
              </div>

              {/* Search destination by name to switch target */}
              <div className="pt-3 border-t border-slate-800/60 space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <input
                    type="text"
                    value={destSearch}
                    onChange={(e) => setDestSearch(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && runDestinationSearch()}
                    placeholder="Search destination by name (e.g. Ilam, Rolpa, Mustang)..."
                    className="flex-1 min-w-[240px] px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-600/60 text-sm text-white placeholder-slate-400 focus:outline-none focus:border-amber-400"
                  />
                  <button onClick={runDestinationSearch} className="px-4 py-2 rounded-lg bg-slate-600 hover:bg-emerald-600 text-white text-sm font-bold">
                    Search
                  </button>
                </div>
                {destSearchResults.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {destSearchResults.map((d) => (
                      <button
                        key={d.id}
                        onClick={() => { setPipelineDestSlug(d.slug || String(d.id)); setPipelineDestId(d.id); setDestSearchResults([]); loadPipelineImages(d.slug || String(d.id), d.id) }}
                        className="px-3 py-1.5 rounded-lg bg-slate-800/70 hover:bg-amber-400 hover:text-gray-950 text-slate-200 text-xs font-semibold border border-slate-600/50"
                      >
                        {d.name} <span className="opacity-60">({d.district || d.province || "—"})</span>
                      </button>
                    ))}
                  </div>
                )}
              </div>

              {/* Destination Selector Pills */}
              <div className="pt-2 border-t border-slate-800/60 flex flex-wrap items-center gap-2">
                <span className="text-xs font-bold text-amber-300">Target Destination:</span>
                {[
                  { label: "Pokhara & Phewa Lake", slug: "phewa-lake-tal-barahi" },
                  { label: "Everest Base Camp", slug: "everest-base-camp-ebc" },
                  { label: "Ruru Kshetra / Ridi", slug: "ruru" },
                  { label: "Tinjure Rhododendron", slug: "tinjure" },
                  { label: "Myanglung Village", slug: "myanglung" },
                  { label: "Milke Danda Ridge", slug: "milke" },
                  { label: "Devi's Fall Pokhara", slug: "devis" },
                  { label: "Nagarkot Sunrise", slug: "nagarkot-himalayan-sunrise-viewpoint" },
                ].map((p, idx) => (
                  <button
                    key={idx}
                    onClick={() => {
                      setPipelineDestSlug(p.slug)
                      setPipelineDestId(null)
                      loadPipelineImages(p.slug)
                    }}
                    className={`px-3 py-1 rounded-lg text-xs font-bold transition-all ${
                      pipelineDestSlug === p.slug
                        ? "bg-amber-400 text-gray-950 shadow"
                        : "bg-slate-800/50 hover:bg-slate-800 text-slate-300 border border-slate-600/50"
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>

              {/* Custom destination slug / ID input */}
              <div className="flex items-center gap-3 pt-2">
                <input
                  type="text"
                  value={pipelineDestSlug}
                  onChange={(e) => setPipelineDestSlug(e.target.value)}
                  placeholder="Enter destination slug or ID (e.g. phewa-lake-tal-barahi)..."
                  className="w-72 px-3 py-1.5 rounded-xl bg-slate-800/60 border border-slate-600/60 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-amber-400"
                />
                <button
                  onClick={() => loadPipelineImages()}
                  className="px-3.5 py-1.5 rounded-xl bg-slate-700 hover:bg-slate-600 text-white font-bold text-xs"
                >
                  Load Images
                </button>
              </div>

              {/* Admin: upload-by-URL + set cover */}
              <div className="mt-3 p-3 rounded-xl bg-slate-900/40 border border-slate-700/60 space-y-2">
                <p className="text-[11px] font-bold text-amber-300">Admin: add / override destination image</p>
                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="text"
                    value={newImageUrl}
                    onChange={(e) => setNewImageUrl(e.target.value)}
                    placeholder="Paste image URL (https://...)"
                    className="flex-1 px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-600/60 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-amber-400"
                  />
                  <input
                    type="text"
                    value={newImageCaption}
                    onChange={(e) => setNewImageCaption(e.target.value)}
                    placeholder="Caption (optional)"
                    className="sm:w-56 px-3 py-2 rounded-lg bg-slate-800/60 border border-slate-600/60 text-xs text-white placeholder-slate-400 focus:outline-none focus:border-amber-400"
                  />
                  <button
                    onClick={handleAddAdminImage}
                    className="px-4 py-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-bold whitespace-nowrap"
                  >
                    + Add &amp; set cover
                  </button>
                </div>
                <div className="flex flex-col sm:flex-row gap-2 pt-2 border-t border-slate-700/60">
                  <input type="file" accept="image/*" onChange={(e)=>setNewImageFile(e.target.files?.[0] || null)} className="flex-1 text-xs text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-700 file:px-3 file:py-2 file:text-white" />
                  <button type="button" disabled={!newImageFile} onClick={handleUploadAdminImage} className="px-4 py-2 rounded-lg bg-blue-600 hover:bg-blue-500 disabled:opacity-40 text-white text-xs font-bold">Browse PC & Upload Cover</button>
                </div>
                {(newImageUrl.trim() || newImageFile) && (
                  <div className="flex items-center gap-3 pt-2">
                    <img
                      src={newImageFile ? URL.createObjectURL(newImageFile) : newImageUrl.trim()}
                      alt="Selected image preview"
                      className="h-24 w-36 rounded-lg object-cover border border-amber-400/50 bg-black"
                      onError={(e) => { e.currentTarget.style.opacity = "0.3" }}
                    />
                    <p className="text-[11px] text-slate-300">Preview of the image that will be saved as the current cover. After upload the gallery below refreshes from the database.</p>
                  </div>
                )}
                <p className="text-[10px] text-slate-300">URL and local-disk uploads save directly to the database and show on the site immediately.</p>
                <div className="pt-3 border-t border-slate-700/60 space-y-2">
                  <p className="text-[11px] font-bold text-sky-300">Admin: destination videos (25 MB max)</p>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <input type="file" accept="video/*" onChange={(e)=>setNewVideoFile(e.target.files?.[0] || null)} className="flex-1 text-xs text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-700 file:px-3 file:py-2 file:text-white" />
                    <button type="button" disabled={!newVideoFile} onClick={async () => {
                      if (!newVideoFile) return
                      if (newVideoFile.size > 25 * 1024 * 1024) return showToast("Videos must be 25 MB or smaller.", "error")
                      const destId = await resolvePipelineDestination()
                      if (!destId) return showToast("Select a destination first.", "error")
                      const form = new FormData()
                      form.append("video_file", newVideoFile)
                      form.append("title", newVideoFile.name)
                      try {
                        await adminApi.addAdminDestinationVideo(destId, form)
                        showToast("Video added.", "success")
                        setNewVideoFile(null)
                        await loadPipelineImages(null, destId)
                      } catch (error) {
                        showToast(error?.response?.data?.detail || "Video upload failed.", "error")
                      }
                    }} className="px-4 py-2 rounded-lg bg-sky-600 hover:bg-sky-500 disabled:opacity-40 text-white text-xs font-bold">Upload video</button>
                  </div>
                  {pipelineVideos.length > 0 && (
                    <div className="grid sm:grid-cols-2 gap-2">
                      {pipelineVideos.map((video) => (
                        <div key={video.id} className="rounded-lg bg-slate-800/80 p-2 text-[11px] text-slate-200">
                          <p className="font-bold truncate">{video.title || video.caption || "Video"} · {video.verification_status}</p>
                          {video.url && <video src={video.url} controls className="mt-1 w-full max-h-32 rounded" />}
                          <div className="mt-1 flex gap-1">
                            <button type="button" onClick={async () => { await adminApi.updateAdminDestinationVideo(pipelineDestId, { video_id: video.id, verification_status: video.verification_status === "approved" ? "pending" : "approved" }); loadPipelineImages() }} className="rounded bg-emerald-700 px-2 py-1 text-white font-bold">{video.verification_status === "approved" ? "Unpublish" : "Approve"}</button>
                            <button type="button" onClick={async () => { if (!window.confirm("Remove this video?")) return; await adminApi.deleteAdminDestinationVideo(pipelineDestId, video.id); loadPipelineImages() }} className="rounded bg-rose-700 px-2 py-1 text-white font-bold">Remove</button>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Strict Commercial Usage-Rights & License Verification Desk Banner */}
            <div className="p-4 rounded-2xl bg-emerald-950/60 border border-emerald-500/40 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
              <div className="space-y-0.5">
                <span className="text-[10px] font-black uppercase text-emerald-300">
                  Google Usage-Rights & Commercial Compliance Policy Active
                </span>
                <p className="text-xs font-bold text-white">
                  ✓ All discovered images verified against commercial reuse terms. Non-commercial (CC BY-NC), All Rights Reserved, and paid stock licenses automatically rejected.
                </p>
              </div>
              <span className="px-3 py-1 rounded-xl bg-emerald-500/20 text-emerald-300 border border-emerald-500/40 text-xs font-black shrink-0">
                100% Commercial Reusable
              </span>
            </div>

            {/* Provenance Stats Bar (All 12 Providers) */}
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 lg:grid-cols-10 gap-2.5">
              <div className="p-3 rounded-2xl bg-slate-900/50 border border-slate-700/40 text-center">
                <span className="text-[10px] uppercase font-black text-slate-300 block">Total</span>
                <p className="text-lg font-black text-white mt-0.5">{pipelineImages.length}</p>
              </div>
              <div className="p-3 rounded-2xl bg-blue-950/50 border border-blue-800/40 text-center">
                <span className="text-[10px] uppercase font-black text-blue-300 block">Wikimedia</span>
                <p className="text-lg font-black text-blue-400 mt-0.5">
                  {pipelineImages.filter((i) => i.source === "wikimedia").length}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-slate-800/50 border border-slate-600/40 text-center">
                <span className="text-[10px] uppercase font-black text-slate-300 block">Openverse</span>
                <p className="text-lg font-black text-emerald-400 mt-0.5">
                  {pipelineImages.filter((i) => i.source === "openverse").length}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-sky-950/50 border border-sky-800/40 text-center">
                <span className="text-[10px] uppercase font-black text-sky-300 block">OSM/Mapillary</span>
                <p className="text-lg font-black text-sky-400 mt-0.5">
                  {pipelineImages.filter((i) => i.source?.includes("osm") || i.source?.includes("mapillary")).length}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-amber-950/50 border border-amber-800/40 text-center">
                <span className="text-[10px] uppercase font-black text-amber-300 block">Nepal Gov/Open</span>
                <p className="text-lg font-black text-amber-400 mt-0.5">
                  {pipelineImages.filter((i) => i.source?.includes("nepal_gov") || i.source?.includes("kaggle") || i.source?.includes("google_landmark")).length}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-teal-950/50 border border-teal-800/40 text-center">
                <span className="text-[10px] uppercase font-black text-teal-300 block">Satellite</span>
                <p className="text-lg font-black text-teal-400 mt-0.5">
                  {pipelineImages.filter((i) => i.source?.includes("satellite")).length}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-emerald-950/50 border border-emerald-800/40 text-center">
                <span className="text-[10px] uppercase font-black text-emerald-300 block">Unsplash</span>
                <p className="text-lg font-black text-emerald-400 mt-0.5">
                  {pipelineImages.filter((i) => i.source === "unsplash").length}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-cyan-950/50 border border-cyan-800/40 text-center">
                <span className="text-[10px] uppercase font-black text-cyan-300 block">Pexels</span>
                <p className="text-lg font-black text-cyan-400 mt-0.5">
                  {pipelineImages.filter((i) => i.source === "pexels").length}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-orange-950/50 border border-orange-800/40 text-center">
                <span className="text-[10px] uppercase font-black text-orange-300 block">Flickr/Pixabay</span>
                <p className="text-lg font-black text-orange-400 mt-0.5">
                  {pipelineImages.filter((i) => i.source === "flickr" || i.source === "pixabay").length}
                </p>
              </div>
              <div className="p-3 rounded-2xl bg-rose-950/50 border border-rose-800/40 text-center">
                <span className="text-[10px] uppercase font-black text-rose-300 block">AI Generated</span>
                <p className="text-lg font-black text-rose-400 mt-0.5">
                  {pipelineImages.filter((i) => i.isAiGenerated).length}
                </p>
              </div>
            </div>

            {/* Image Grid with Provenance Cards */}
            {pipelineLoading ? (
              <div className="py-16 text-center text-slate-300">
                <FiRefreshCw className="animate-spin mx-auto mb-2 text-amber-400" size={32} />
                <p className="font-bold">Executing multi-source image acquisition waterfall chain...</p>
              </div>
            ) : pipelineImages.length === 0 ? (
              <div className="p-12 text-center rounded-3xl bg-slate-900/40 border border-slate-700/40 text-slate-300">
                <p className="font-bold">No images discovered yet for destination '{pipelineDestSlug}'.</p>
                <p className="text-xs text-slate-300 mt-1">Click "Find Images (Multi-Source Pipeline)" above to launch automated discovery!</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                {pipelineImages.map((img, idx) => (
                  <div
                    key={idx}
                    className="rounded-2xl bg-slate-900/60 border border-slate-700/60 overflow-hidden flex flex-col justify-between"
                  >
                    <div className="relative h-44 bg-slate-800">
                      <img
                        src={img.url}
                        alt={img.caption || img.author}
                        className="w-full h-full object-cover"
                        onError={(e) => {
                          e.target.onerror = null
                          e.target.src = "/images/destinations/patan/durbar-square.jpg"
                        }}
                      />
                      <div className="absolute top-2 left-2">
                        <span
                          className={`px-2 py-0.5 rounded-full text-[10px] font-black uppercase tracking-wider shadow ${
                            img.isAiGenerated
                              ? "bg-rose-600 text-white animate-pulse"
                              : img.source === "wikimedia"
                              ? "bg-blue-600 text-white"
                              : img.source === "openverse"
                              ? "bg-emerald-600 text-white"
                              : img.source === "unsplash"
                              ? "bg-emerald-600 text-white"
                              : "bg-amber-500 text-gray-950"
                          }`}
                        >
                          {img.isAiGenerated ? "🤖 AI ILLUSTRATION" : img.source?.toUpperCase()}
                        </span>
                      </div>
                      <div className="absolute bottom-2 right-2">
                        <span className="px-2 py-0.5 rounded bg-black/70 text-white text-[10px] font-mono">
                          {img.license}
                        </span>
                      </div>
                    </div>

                    <div className="p-3.5 space-y-2 flex-1 flex flex-col justify-between">
                      <div>
                        <p className="font-bold text-xs text-white line-clamp-1">{img.caption || "Verified Destination Media"}</p>
                        <p className="text-[11px] text-slate-300 mt-0.5">Author: <span className="text-white font-semibold">{img.author}</span></p>
                      </div>

                      <div className="pt-2 border-t border-slate-800/60 flex items-center justify-between text-[11px] gap-2">
                        <a
                          href={img.sourceUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="text-amber-300 hover:underline font-bold shrink-0"
                        >
                          [View Source]
                        </a>
                        {img.id ? (
                          <button
                            type="button"
                            onClick={async () => {
                              try {
                                await adminApi.setDestinationCover(pipelineDestSlug, img.id)
                                showToast("Cover image updated (rollback applied).", "success")
                                loadPipelineImages()
                              } catch {
                                showToast("Could not set cover image.", "error")
                              }
                            }}
                            className="px-2 py-1 rounded-md bg-emerald-600 hover:bg-emerald-500 text-white text-[10px] font-bold"
                          >
                            Set as cover
                          </button>
                        ) : null}
                        {img.id && <button type="button" onClick={async()=>{await adminApi.updateAdminDestinationImage(pipelineDestId,{image_id:img.id,verification_status:img.verification_status==="rejected"?"approved":"rejected",is_verified:img.verification_status==="rejected"});loadPipelineImages()}} className="px-2 py-1 rounded-md bg-slate-600 text-white text-[10px] font-bold">{img.verification_status==="rejected"?"Enable":"Disable"}</button>}
                        {img.id && <button type="button" onClick={async()=>{await adminApi.updateAdminDestinationImage(pipelineDestId,{image_id:img.id,ordering:Math.max(0,idx-1)});loadPipelineImages()}} className="px-2 py-1 rounded-md bg-blue-600 text-white text-[10px] font-bold">Move up</button>}
                        {img.id && (
                          <button
                            type="button"
                            onClick={() => handleDeleteImage(img.id)}
                            className="px-2 py-1 rounded-md bg-rose-600 hover:bg-rose-500 text-white text-[10px] font-bold"
                          >
                            Remove
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* TAB 6: MEDICAL SOS */}
        {activeTab === "emergencies" && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            <div className="bg-rose-950/50 border border-rose-700/60 p-5 rounded-2xl flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg text-white flex items-center gap-2">
                  <FiAlertTriangle className="text-rose-400" /> Live Medical & SOS Emergency Response
                </h3>
                <p className="text-xs text-rose-200">
                  Immediate 24/7 rescue & hospital coordination dispatch center for tourists in distress across Nepal.
                </p>
              </div>
              <span className="px-3 py-1 rounded-full bg-rose-600 text-white font-bold text-xs">
                {emergencies.filter(e => e.status === "active").length} Active SOS
              </span>
            </div>

            <div className="space-y-4">
              {emergencies.map((e) => (
                <div
                  key={e.id}
                  className={`p-5 rounded-2xl border flex flex-col md:flex-row md:items-center justify-between gap-4 shadow-xl ${
                    e.status === "active"
                      ? "bg-rose-950/70 border-rose-500 shadow-rose-500/20"
                      : "bg-slate-900/60 border-slate-600/40 opacity-80"
                  }`}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        e.status === "active" ? "bg-rose-600 text-white animate-pulse" : "bg-gray-700 text-gray-300"
                      }`}>
                        {e.status.toUpperCase()}
                      </span>
                      <h4 className="font-bold text-white">{e.user_name} ({e.user_email})</h4>
                    </div>
                    <p className="text-sm text-slate-200 font-medium">{e.message}</p>
                    <p className="text-xs text-slate-300 flex items-center gap-3">
                      {e.user_phone && <span>📞 Phone: <b>{e.user_phone}</b></span>}
                      {e.latitude && <span>📍 GPS: <b>{e.latitude.toFixed(4)}, {e.longitude.toFixed(4)}</b></span>}
                      <span>🕒 {new Date(e.triggered_at).toLocaleString()}</span>
                    </p>
                  </div>

                  {e.status === "active" && (
                    <button
                      onClick={() => handleResolveEmergency(e.id)}
                      className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-xs flex items-center gap-2 shadow-lg shadow-emerald-500/30 shrink-0"
                    >
                      <FiCheck size={16} /> Mark Resolved (Green)
                    </button>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {activeTab === "infrastructure" && (
          <div className="space-y-6">
            <ServicePhotosPanel />
            <InfrastructureModerationPanel />
          </div>
        )}
        {activeTab === "hotel_bookings" && <HotelBookingPanel />}
        {activeTab === "marketplace" && <MarketplacePanel />}
        {activeTab === "travel_services" && <TravelServicesPanel />}
        {activeTab === "review_moderation" && <ReviewModerationPanel />}
        {activeTab === "safety_management" && <SafetyManagementPanel />}
        {activeTab === "notification_settings" && <NotificationSettingsPanel />}
        {activeTab === "retention" && <RetentionPolicyPanel />}
        {activeTab === "media_library" && <MediaLibraryPanel />}
        {activeTab === "datasets" && <DatasetManagerPanel />}
        {activeTab === "feedback_workspace" && <FeedbackWorkspace />}

        {/* TAB 7: EXPENSES */}
        {activeTab === "expenses" && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            <div className="bg-slate-900/60 border border-slate-600/40 p-5 rounded-2xl flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg text-white flex items-center gap-2">
                  <FiDollarSign className="text-amber-400" /> Traveler & Employee Field Expenditure Data ({expenseReports.length})
                </h3>
                <p className="text-xs text-slate-300">
                  Connects directly to the ML travel budget engine so future cost estimations learn and calibrate against actual ground costs.
                </p>
              </div>
              <button
                onClick={() => setShowAddExpenseModal(true)}
                className="px-4 py-2.5 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 font-bold text-xs flex items-center gap-2 shadow-lg shadow-amber-400/20"
              >
                <FiPlus size={14} /> Submit Field Expense
              </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {expenseReports.map((exp) => (
                <div key={exp.id} className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5 shadow-xl space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-white text-base">{exp.destination_name}</h4>
                      <p className="text-xs text-slate-300">{exp.num_days} Days · {exp.num_people} Traveler{exp.num_people > 1 ? "s" : ""}</p>
                    </div>
                    <span className="text-xl font-black text-amber-300">
                      NPR {Number(exp.total_cost).toLocaleString()}
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-800/40 text-xs text-slate-300 grid grid-cols-2 gap-2">
                    <p>🏨 Stay: <b>NPR {exp.accommodation_cost}</b></p>
                    <p>🚗 Transit: <b>NPR {exp.travel_cost}</b></p>
                    <p>🍛 Food: <b>NPR {exp.food_cost}</b></p>
                    <p>🎟️ Entry: <b>NPR {exp.entry_cost}</b></p>
                  </div>

                  {exp.route_details && (
                    <p className="text-[11px] text-slate-300">🛣️ <b>Route:</b> {exp.route_details}</p>
                  )}

                  <div className="pt-2 border-t border-slate-700/40 flex items-center justify-between text-[10px] text-emerald-400">
                    <span>By: {exp.user_name || "Field Officer"}</span>
                    {exp.is_employee_verified && <span className="text-emerald-400 font-bold">✓ Field Verified</span>}
                  </div>
                </div>
              ))}
            </div>
          </motion.div>
        )}

        {/* TAB 8: RISKS */}
        {activeTab === "risks" && (
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="space-y-6"
          >
            <div className="bg-slate-900/60 border border-slate-600/40 p-5 rounded-2xl flex items-center justify-between">
              <div>
                <h3 className="font-bold text-lg text-white flex items-center gap-2">
                  <FiShield className="text-pink-400" /> Traveler Safety & Risk Incident Assessments ({riskReports.length})
                </h3>
                <p className="text-xs text-slate-300">
                  Traveler and field survey feedback (AMS sickness, hazards, local hospitality, transport accessibility) dynamically calibrating ML risk indices.
                </p>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
              {riskReports.map((r) => (
                <div key={r.id} className="bg-slate-900/70 border border-slate-600/40 rounded-2xl p-5 shadow-xl space-y-3">
                  <div className="flex items-start justify-between">
                    <div>
                      <h4 className="font-bold text-white text-base">{r.destination_name}</h4>
                      <p className="text-xs text-slate-300">By: {r.user_name || "Traveler"}</p>
                    </div>
                    <span className="px-2.5 py-1 rounded-full text-xs font-extrabold bg-amber-400/20 text-amber-300 border border-amber-400/40">
                      Safety: {r.overall_safety_rating}/10
                    </span>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-800/40 text-xs text-slate-300 space-y-1.5">
                    <p>🤒 Became Sick: <b className={r.became_sick ? "text-rose-400" : "text-emerald-400"}>{r.became_sick ? `Yes (${r.sickness_type})` : "No"}</b></p>
                    <p>⚠️ Hazard Witnessed: <b>{r.hazard_witnessed || "None"}</b></p>
                    <p>🚗 Transport Ease: <b>{r.transport_accessibility_rating} / 5</b></p>
                    <p>🤝 Local Helpfulness: <b>{r.people_helpfulness_rating} / 5</b></p>
                    <p>🙏 Greeting & Hospitality: <b>{r.greeting_behavior_rating} / 5</b></p>
                  </div>

                  {r.comments && (
                    <p className="text-xs text-slate-300 italic">"{r.comments}"</p>
                  )}
                </div>
              ))}
            </div>
          </motion.div>
        )}
      </div>

      {/* MODAL 1: FULL DETAIL PLACE INSPECTION BEFORE ACCEPT/REJECT */}
      <AnimatePresence>
        {inspectingPlace && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-emerald-600/50 rounded-3xl p-6 sm:p-8 max-w-3xl w-full shadow-2xl space-y-6 text-white max-h-[90vh] overflow-y-auto"
            >
              <div className="flex items-start justify-between border-b border-slate-600/60 pb-4">
                <div>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-400 text-gray-950">
                    {inspectingPlace.category_name}
                  </span>
                  <h2 className="text-2xl font-black text-white mt-1">{inspectingPlace.name}</h2>
                  <p className="text-xs text-slate-300">
                    Submitted by: <b>{inspectingPlace.created_by}</b> · {new Date(inspectingPlace.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={() => setInspectingPlace(null)}
                  className="p-2 rounded-full bg-slate-800/60 hover:bg-slate-700 text-slate-300"
                >
                  <FiX size={20} />
                </button>
              </div>

              {/* Submitted Pictures */}
              {inspectingPlace.cover_image_url && (
                <div className="h-64 rounded-2xl overflow-hidden border border-slate-600 shadow-lg">
                  <img src={inspectingPlace.cover_image_url} alt={inspectingPlace.name} className="w-full h-full object-cover" />
                </div>
              )}

              {/* Administrative & Coordinate Details */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 p-4 rounded-2xl bg-slate-900/80 border border-slate-600/50 text-xs">
                <div>
                  <span className="text-slate-300">Province</span>
                  <p className="font-bold text-white mt-0.5">{inspectingPlace.province || "Gandaki"}</p>
                </div>
                <div>
                  <span className="text-slate-300">District / City</span>
                  <p className="font-bold text-white mt-0.5">{inspectingPlace.district || inspectingPlace.city}</p>
                </div>
                <div>
                  <span className="text-slate-300">Municipality</span>
                  <p className="font-bold text-white mt-0.5">{inspectingPlace.municipality || "N/A"}</p>
                </div>
                <div>
                  <span className="text-slate-300">Ward Number</span>
                  <p className="font-bold text-white mt-0.5">{inspectingPlace.ward_number ? `Ward ${inspectingPlace.ward_number}` : "N/A"}</p>
                </div>
                <div>
                  <span className="text-slate-300">Latitude</span>
                  <p className="font-bold text-amber-300 mt-0.5">{inspectingPlace.latitude?.toFixed(6)}</p>
                </div>
                <div>
                  <span className="text-slate-300">Longitude</span>
                  <p className="font-bold text-amber-300 mt-0.5">{inspectingPlace.longitude?.toFixed(6)}</p>
                </div>
                <div>
                  <span className="text-slate-300">Altitude</span>
                  <p className="font-bold text-cyan-300 mt-0.5">{inspectingPlace.altitude || "N/A"}</p>
                </div>
                <div>
                  <span className="text-slate-300">Entry Fee</span>
                  <p className="font-bold text-emerald-300 mt-0.5">NPR {inspectingPlace.entry_fee || 0}</p>
                </div>
              </div>

              {/* Text content */}
              <div className="space-y-3 text-xs">
                <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-700">
                  <h4 className="font-bold text-amber-300 mb-1">Full Description:</h4>
                  <p className="text-slate-200 leading-relaxed whitespace-pre-line">{inspectingPlace.description}</p>
                </div>

                {inspectingPlace.history && (
                  <div className="p-4 rounded-2xl bg-slate-900/60 border border-slate-700">
                    <h4 className="font-bold text-amber-300 mb-1">Historical & Cultural Heritage:</h4>
                    <p className="text-slate-200 leading-relaxed whitespace-pre-line">{inspectingPlace.history}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-700">
                    <h5 className="font-bold text-slate-300">🏥 Nearest Hospital</h5>
                    <p className="text-slate-200 mt-1">{inspectingPlace.nearest_hospital_info || "None specified"}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-700">
                    <h5 className="font-bold text-slate-300">🏨 Nearest Hotel</h5>
                    <p className="text-slate-200 mt-1">{inspectingPlace.nearest_hotel_info || "None specified"}</p>
                  </div>
                  <div className="p-3 rounded-xl bg-slate-900/60 border border-slate-700">
                    <h5 className="font-bold text-slate-300">👮 Police Station</h5>
                    <p className="text-slate-200 mt-1">{inspectingPlace.nearest_police_info || "None specified"}</p>
                  </div>
                </div>
              </div>

              {/* ACTION BUTTONS (GREEN Accept & RED Reject) */}
              <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-600/60">
                <button
                  onClick={() => handleRejectPlace(inspectingPlace.id)}
                  className="px-6 py-3 rounded-2xl bg-rose-600 hover:bg-rose-700 text-white font-bold text-xs flex items-center gap-2 shadow-xl shadow-rose-600/30 transition-all"
                >
                  <FiX size={16} /> Reject Place (Red)
                </button>
                <button
                  onClick={() => handleApprovePlace(inspectingPlace.id)}
                  className="px-8 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-600 text-white font-black text-xs flex items-center gap-2 shadow-xl shadow-emerald-500/30 transition-all"
                >
                  <FiCheck size={18} /> Accept & Publish to Database (Green)
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL 2: USER TRAVEL HISTORY TIMELINE */}
      <AnimatePresence>
        {selectedUserHistory && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-emerald-600/50 rounded-3xl p-6 sm:p-8 max-w-xl w-full shadow-2xl space-y-5 text-white max-h-[85vh] overflow-y-auto"
            >
              <div className="flex items-start justify-between border-b border-slate-600/60 pb-3">
                <div>
                  <h3 className="text-xl font-bold text-white">{selectedUserHistory.full_name || selectedUserHistory.email}</h3>
                  <p className="text-xs text-slate-300">User Profile & Travel History Log</p>
                </div>
                <button onClick={() => setSelectedUserHistory(null)} className="text-slate-300 hover:text-white">
                  <FiX size={20} />
                </button>
              </div>

              <div className="p-4 rounded-2xl bg-slate-900/80 border border-slate-700 text-xs space-y-2">
                <p className="text-amber-300 font-bold">Profile Bio / Description:</p>
                <p className="text-slate-200 italic">"{selectedUserHistory.bio}"</p>
                <div className="pt-2 flex justify-between text-slate-300 text-[11px]">
                  <span>Role: <b>{selectedUserHistory.role}</b></span>
                  <span>Registered: <b>{new Date(selectedUserHistory.date_joined).toLocaleDateString()}</b></span>
                </div>
              </div>

              <div className="space-y-3">
                <h4 className="font-bold text-sm text-amber-300 flex items-center gap-1.5">
                  <FiMapPin /> Destinations Visited ({selectedUserHistory.travel_history?.length || 0})
                </h4>

                {selectedUserHistory.travel_history?.length === 0 ? (
                  <p className="text-xs text-emerald-400 italic">No destination visits recorded yet.</p>
                ) : (
                  <div className="space-y-2 max-h-60 overflow-y-auto pr-1">
                    {selectedUserHistory.travel_history?.map((item, idx) => (
                      <div key={idx} className="p-3 rounded-xl bg-slate-900/60 border border-slate-700/50 flex items-center justify-between text-xs">
                        <div>
                          <p className="font-bold text-white">{item.destination__name}</p>
                          <p className="text-[10px] text-slate-300">{item.destination__city || "Nepal"}</p>
                        </div>
                        <span className="text-[10px] text-amber-300/80">
                          {new Date(item.viewed_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL 3: ADD SUB-ADMIN / STAFF */}
      <AnimatePresence>
        {showAddUserModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-slate-600/50 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-5 text-white"
            >
              <div className="flex items-center justify-between border-b border-slate-700 pb-3">
                <h3 className="text-lg font-bold">Add New User or Assign Sub-Admin</h3>
                <button onClick={() => setShowAddUserModal(false)} className="text-slate-300 hover:text-white">
                  <FiX size={20} />
                </button>
              </div>

              <form onSubmit={handleCreateUser} className="space-y-4 text-xs">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300">First Name</label>
                    <input
                      className="input-field mt-1 text-xs text-gray-900"
                      value={newUserForm.first_name}
                      onChange={(e) => setNewUserForm({ ...newUserForm, first_name: e.target.value })}
                      placeholder="e.g. Ramesh"
                    />
                  </div>
                  <div>
                    <label className="text-slate-300">Last Name</label>
                    <input
                      className="input-field mt-1 text-xs text-gray-900"
                      value={newUserForm.last_name}
                      onChange={(e) => setNewUserForm({ ...newUserForm, last_name: e.target.value })}
                      placeholder="e.g. Shrestha"
                    />
                  </div>
                </div>

                <div>
                  <label className="text-slate-300">Email Address *</label>
                  <input
                    type="email"
                    required
                    className="input-field mt-1 text-xs text-gray-900"
                    value={newUserForm.email}
                    onChange={(e) => setNewUserForm({ ...newUserForm, email: e.target.value })}
                    placeholder="staff@nepaltourism.gov.np"
                  />
                </div>

                <div>
                  <label className="text-slate-300">Password *</label>
                  <input
                    type="password"
                    required
                    className="input-field mt-1 text-xs text-gray-900"
                    value={newUserForm.password}
                    onChange={(e) => setNewUserForm({ ...newUserForm, password: e.target.value })}
                    placeholder="Minimum 8 characters"
                  />
                </div>

                <div>
                  <label className="text-slate-300">User Description / Bio</label>
                  <textarea
                    rows={2}
                    className="input-field mt-1 text-xs text-gray-900"
                    value={newUserForm.bio}
                    onChange={(e) => setNewUserForm({ ...newUserForm, bio: e.target.value })}
                    placeholder="Travel interests, duties, or district assignments..."
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300">Assign Role (RBAC)</label>
                    <select
                      className="input-field mt-1 text-xs text-gray-900"
                      value={newUserForm.role}
                      onChange={(e) => setNewUserForm({ ...newUserForm, role: e.target.value })}
                    >
                      {ROLES.map((r) => (
                        <option key={r.id} value={r.id}>{r.label}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="text-slate-300">Managed District</label>
                    <input
                      className="input-field mt-1 text-xs text-gray-900"
                      value={newUserForm.managed_district}
                      onChange={(e) => setNewUserForm({ ...newUserForm, managed_district: e.target.value })}
                      placeholder="e.g. Kaski / Mustang"
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setShowAddUserModal(false)}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 text-xs font-bold shadow-lg shadow-amber-400/20"
                  >
                    Create User / Sub-Admin
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* MODAL 4: SUBMIT FIELD EXPENSE (ML CONNECTION) */}
      <AnimatePresence>
        {showAddExpenseModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 border border-slate-600/50 rounded-2xl p-6 max-w-lg w-full shadow-2xl space-y-4 text-white"
            >
              <div className="flex items-center justify-between border-b border-slate-700 pb-3">
                <h3 className="text-lg font-bold">Record Field Expense (ML Feedback)</h3>
                <button onClick={() => setShowAddExpenseModal(false)} className="text-slate-300 hover:text-white">
                  <FiX size={20} />
                </button>
              </div>

              <form onSubmit={handleSubmitExpense} className="space-y-3 text-xs">
                <div>
                  <label className="text-slate-300">Destination Name *</label>
                  <input
                    required
                    className="input-field mt-1 text-xs text-gray-900"
                    value={expenseForm.destination_name}
                    onChange={(e) => setExpenseForm({ ...expenseForm, destination_name: e.target.value })}
                    placeholder="e.g. Annapurna Base Camp / Mustang"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300">Number of Travelers</label>
                    <input
                      type="number"
                      min={1}
                      className="input-field mt-1 text-xs text-gray-900"
                      value={expenseForm.num_people}
                      onChange={(e) => setExpenseForm({ ...expenseForm, num_people: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <label className="text-slate-300">Number of Days</label>
                    <input
                      type="number"
                      min={1}
                      className="input-field mt-1 text-xs text-gray-900"
                      value={expenseForm.num_days}
                      onChange={(e) => setExpenseForm({ ...expenseForm, num_days: Number(e.target.value) })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300">Stay Cost (NPR)</label>
                    <input
                      type="number"
                      className="input-field mt-1 text-xs text-gray-900"
                      value={expenseForm.accommodation_cost}
                      onChange={(e) => setExpenseForm({ ...expenseForm, accommodation_cost: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <label className="text-slate-300">Transit Cost (NPR)</label>
                    <input
                      type="number"
                      className="input-field mt-1 text-xs text-gray-900"
                      value={expenseForm.travel_cost}
                      onChange={(e) => setExpenseForm({ ...expenseForm, travel_cost: Number(e.target.value) })}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-slate-300">Food Cost (NPR)</label>
                    <input
                      type="number"
                      className="input-field mt-1 text-xs text-gray-900"
                      value={expenseForm.food_cost}
                      onChange={(e) => setExpenseForm({ ...expenseForm, food_cost: Number(e.target.value) })}
                    />
                  </div>
                  <div>
                    <label className="text-slate-300">Entry / Permit (NPR)</label>
                    <input
                      type="number"
                      className="input-field mt-1 text-xs text-gray-900"
                      value={expenseForm.entry_cost}
                      onChange={(e) => setExpenseForm({ ...expenseForm, entry_cost: Number(e.target.value) })}
                    />
                  </div>
                </div>

                <div className="flex justify-end gap-3 pt-3 border-t border-slate-700">
                  <button
                    type="button"
                    onClick={() => setShowAddExpenseModal(false)}
                    className="px-4 py-2 rounded-xl bg-slate-800 hover:bg-slate-700 text-slate-300 text-xs font-semibold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-5 py-2 rounded-xl bg-amber-400 hover:bg-amber-500 text-gray-950 text-xs font-bold shadow-lg shadow-amber-400/20"
                  >
                    Feed into ML Engine
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default AdminDashboard
