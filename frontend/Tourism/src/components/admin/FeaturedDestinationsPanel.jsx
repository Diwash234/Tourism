import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import {
  FiStar, FiPlus, FiTrash2, FiEdit3, FiArrowUp, FiArrowDown,
  FiCheck, FiX, FiSearch, FiEye, FiImage, FiExternalLink, FiCompass,
  FiCalendar, FiCheckCircle, FiInfo, FiSliders
} from "react-icons/fi"
import adminApi from "../../api/adminApi"
import destinationApi from "../../api/destinationApi"
import useToast from "../../hooks/useToast"

export default function FeaturedDestinationsPanel() {
  const { showToast } = useToast()

  const [cards, setCards] = useState([])
  const [loading, setLoading] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  // Destination autocomplete search for adding new
  const [destSearch, setDestSearch] = useState("")
  const [destResults, setDestSearchResults] = useState([])
  const [selectedDest, setSelectedDest] = useState(null)
  const [destGallery, setDestGallery] = useState([])

  // Modal / Form state
  const [showModal, setShowModal] = useState(false)
  const [editingCard, setEditingCard] = useState(null)

  const [form, setForm] = useState({
    title: "",
    short_description: "",
    featured_media_id: null,
    featured_media_url: "",
    cta_label: "Explore Destination",
    cta_url: "",
    display_order: 0,
    is_published: true,
    publish_start: "",
    publish_end: "",
  })

  const loadFeatured = () => {
    setLoading(true)
    adminApi.getFeaturedDestinations({ q: searchQuery })
      .then(({ data }) => {
        setCards(data.results || data || [])
      })
      .catch(() => setCards([]))
      .finally(() => setLoading(false))
  }

  useEffect(() => {
    loadFeatured()
  }, [searchQuery])

  // Destination search
  useEffect(() => {
    if (!destSearch.trim() || destSearch.length < 2) {
      setDestSearchResults([])
      return
    }
    const timer = setTimeout(() => {
      destinationApi.getDestinations({ search: destSearch, page_size: 8 })
        .then(({ data }) => {
          setDestSearchResults(data.results || data || [])
        })
        .catch(() => setDestSearchResults([]))
    }, 250)
    return () => clearTimeout(timer)
  }, [destSearch])

  // When a destination is selected, fetch its images for gallery selection
  const handleSelectDestination = async (dest) => {
    setSelectedDest(dest)
    setDestSearchResults([])
    setDestSearch("")
    if (!editingCard) {
      setForm((prev) => ({
        ...prev,
        title: dest.name || "",
        short_description: dest.short_description || dest.description || "",
        cta_url: `/destinations/${dest.slug}`,
      }))
    }
    try {
      const { data } = await adminApi.getAdminDestination(dest.id)
      setDestGallery(data.gallery || [])
    } catch {
      setDestGallery([])
    }
  }

  const handleOpenAddModal = () => {
    setEditingCard(null)
    setSelectedDest(null)
    setDestGallery([])
    setForm({
      title: "",
      short_description: "",
      featured_media_id: null,
      featured_media_url: "",
      cta_label: "Explore Destination",
      cta_url: "",
      display_order: cards.length + 1,
      is_published: true,
      publish_start: "",
      publish_end: "",
    })
    setShowModal(true)
  }

  const handleOpenEditModal = async (card) => {
    setEditingCard(card)
    setSelectedDest({
      id: card.destination,
      name: card.destination_name,
      slug: card.destination_slug,
      city: card.destination_city,
      province: card.destination_province,
    })
    setForm({
      title: card.title || "",
      short_description: card.short_description || "",
      featured_media_id: card.featured_media || null,
      featured_media_url: card.featured_media_url || "",
      cta_label: card.cta_label || "Explore Destination",
      cta_url: card.cta_url || `/destinations/${card.destination_slug}`,
      display_order: card.display_order ?? 0,
      is_published: card.is_published ?? true,
      publish_start: card.publish_start ? card.publish_start.slice(0, 16) : "",
      publish_end: card.publish_end ? card.publish_end.slice(0, 16) : "",
    })
    setShowModal(true)
    try {
      const { data } = await adminApi.getAdminDestination(card.destination)
      setDestGallery(data.gallery || [])
    } catch {
      setDestGallery([])
    }
  }

  const handleSave = async (e) => {
    e.preventDefault()
    if (!selectedDest && !editingCard) {
      return showToast("Please select an existing destination to feature.", "error")
    }

    const payload = {
      destination_id: selectedDest ? selectedDest.id : editingCard.destination,
      title: form.title,
      short_description: form.short_description,
      featured_media: form.featured_media_id || null,
      featured_media_url: form.featured_media_url,
      cta_label: form.cta_label || "Explore Destination",
      cta_url: form.cta_url,
      display_order: Number(form.display_order) || 0,
      is_published: form.is_published,
      publish_start: form.publish_start ? new Date(form.publish_start).toISOString() : null,
      publish_end: form.publish_end ? new Date(form.publish_end).toISOString() : null,
    }

    try {
      if (editingCard) {
        await adminApi.updateFeaturedDestination(editingCard.id, payload)
        showToast("Featured destination card updated!", "success")
      } else {
        await adminApi.createFeaturedDestination(payload)
        showToast("Destination promoted as featured card!", "success")
      }
      setShowModal(false)
      loadFeatured()
    } catch (err) {
      const msg = err.response?.data?.destination_id || err.response?.data?.detail || "Save failed. Check input fields."
      showToast(Array.isArray(msg) ? msg[0] : String(msg), "error")
    }
  }

  const handleUnfeature = async (card) => {
    if (!confirm(`Unfeature "${card.effective_title}"? This removes the promotional card from the featured section, but preserves the underlying destination.`)) return
    try {
      await adminApi.deleteFeaturedDestination(card.id)
      showToast(`Unfeatured "${card.effective_title}". Destination preserved.`, "info")
      loadFeatured()
    } catch {
      showToast("Could not unfeature destination.", "error")
    }
  }

  const handleMoveOrder = async (idx, direction) => {
    const targetIdx = direction === "up" ? idx - 1 : idx + 1
    if (targetIdx < 0 || targetIdx >= cards.length) return

    const reordered = [...cards]
    const temp = reordered[idx]
    reordered[idx] = reordered[targetIdx]
    reordered[targetIdx] = temp

    const items = reordered.map((item, i) => ({ id: item.id, display_order: i + 1 }))

    try {
      await adminApi.reorderFeaturedDestinations(items)
      showToast("Featured card display order updated!", "success")
      loadFeatured()
    } catch {
      showToast("Could not reorder cards.", "error")
    }
  }

  const handleTogglePublish = async (card) => {
    try {
      await adminApi.updateFeaturedDestination(card.id, { is_published: !card.is_published })
      showToast(`Card ${!card.is_published ? "published" : "unpublished"}`, "success")
      loadFeatured()
    } catch {
      showToast("Could not update status", "error")
    }
  }

  return (
    <div className="space-y-6 text-slate-100">
      {/* Top Header & Stats */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 bg-slate-950 p-6 rounded-3xl border border-slate-800 shadow-xl">
        <div>
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-bold uppercase tracking-wider">
            <FiStar size={14} /> Content Publishing Studio
          </div>
          <h2 className="text-2xl font-black text-white mt-1">Featured Destinations Studio</h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Configure featured cards, media, and calls-to-action on top of existing destination records.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleOpenAddModal}
            className="px-5 py-2.5 rounded-2xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-black text-xs flex items-center gap-2 shadow-lg shadow-amber-400/20 transition-all"
          >
            <FiPlus size={16} /> Feature a Destination
          </button>
        </div>
      </div>

      {/* Control Bar: Search & Status Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
        <div className="md:col-span-2 relative">
          <FiSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search featured cards by title, description or destination..."
            className="w-full pl-11 pr-4 py-3 rounded-2xl bg-slate-900 border border-slate-700 text-xs text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
          />
        </div>

        <div className="flex items-center justify-around p-3 rounded-2xl bg-slate-900 border border-slate-800 text-xs">
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Total Featured</span>
            <span className="text-lg font-black text-white">{cards.length}</span>
          </div>
          <div className="h-6 w-px bg-slate-800" />
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Live Published</span>
            <span className="text-lg font-black text-emerald-400">{cards.filter(c => c.is_published).length}</span>
          </div>
          <div className="h-6 w-px bg-slate-800" />
          <div>
            <span className="text-slate-400 block text-[10px] uppercase font-bold">Draft / Hidden</span>
            <span className="text-lg font-black text-amber-300">{cards.filter(c => !c.is_published).length}</span>
          </div>
        </div>
      </div>

      {/* Featured Cards List */}
      {loading ? (
        <div className="p-12 text-center text-slate-400">
          <p className="font-bold text-sm">Loading featured destination cards...</p>
        </div>
      ) : cards.length === 0 ? (
        <div className="p-12 text-center rounded-3xl bg-slate-950 border border-slate-800 text-slate-400 space-y-3">
          <FiStar className="mx-auto text-amber-400 opacity-60" size={36} />
          <h3 className="text-lg font-bold text-white">No Featured Destinations Configured</h3>
          <p className="text-xs max-w-md mx-auto">
            Promote destinations on the homepage and discovery sections by creating custom featured cards.
          </p>
          <button
            onClick={handleOpenAddModal}
            className="px-5 py-2.5 rounded-2xl bg-amber-400 text-slate-950 font-bold text-xs inline-flex items-center gap-2"
          >
            <FiPlus /> Add First Featured Card
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {cards.map((card, idx) => (
            <motion.div
              key={card.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`rounded-3xl bg-slate-950 border overflow-hidden flex flex-col justify-between shadow-xl transition-all ${
                card.is_published ? "border-slate-800 hover:border-slate-700" : "border-amber-900/40 opacity-75"
              }`}
            >
              {/* Card Image & Header Badges */}
              <div className="relative h-48 bg-slate-900 overflow-hidden">
                <img
                  src={card.effective_image_url || "/images/destinations/annapurna/img1.jpg"}
                  alt={card.effective_title}
                  className="w-full h-full object-cover"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-slate-950 via-transparent to-black/40" />

                {/* Status & Position Badges */}
                <div className="absolute top-3 left-3 flex gap-2">
                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-black uppercase tracking-wider ${
                    card.is_published ? "bg-emerald-500 text-slate-950" : "bg-amber-500 text-slate-950"
                  }`}>
                    {card.is_published ? "✓ Published" : "Draft"}
                  </span>
                  <span className="px-2.5 py-1 rounded-full bg-black/70 backdrop-blur text-amber-300 text-[10px] font-mono font-bold">
                    Order #{card.display_order ?? idx + 1}
                  </span>
                </div>

                {/* Reorder Buttons */}
                <div className="absolute top-3 right-3 flex gap-1">
                  <button
                    disabled={idx === 0}
                    onClick={() => handleMoveOrder(idx, "up")}
                    className="p-1.5 rounded-xl bg-black/60 hover:bg-black text-white disabled:opacity-30 backdrop-blur"
                    title="Move Up"
                  >
                    <FiArrowUp size={14} />
                  </button>
                  <button
                    disabled={idx === cards.length - 1}
                    onClick={() => handleMoveOrder(idx, "down")}
                    className="p-1.5 rounded-xl bg-black/60 hover:bg-black text-white disabled:opacity-30 backdrop-blur"
                    title="Move Down"
                  >
                    <FiArrowDown size={14} />
                  </button>
                </div>

                {/* Underlying Destination Tag */}
                <div className="absolute bottom-3 left-3 right-3">
                  <span className="text-[11px] font-bold text-amber-300 block truncate">
                    📍 {card.destination_name} ({card.destination_city || card.destination_district}, {card.destination_province})
                  </span>
                </div>
              </div>

              {/* Card Body */}
              <div className="p-5 space-y-3 flex-1 flex flex-col justify-between">
                <div className="space-y-1.5">
                  <h3 className="text-lg font-black text-white leading-snug">
                    {card.effective_title}
                  </h3>
                  <p className="text-xs text-slate-400 line-clamp-3 leading-relaxed">
                    {card.effective_description}
                  </p>
                </div>

                <div className="pt-3 border-t border-slate-800/80 space-y-3">
                  {/* CTA Preview */}
                  <div className="flex items-center justify-between text-xs">
                    <span className="text-[11px] font-bold text-slate-400">Call-to-Action:</span>
                    <span className="px-3 py-1 rounded-xl bg-amber-400/10 border border-amber-400/30 text-amber-300 font-bold text-[11px]">
                      {card.cta_label || "Explore Destination"} →
                    </span>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between gap-2 pt-2 border-t border-slate-900">
                    <button
                      onClick={() => handleTogglePublish(card)}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold ${
                        card.is_published ? "bg-slate-800 text-slate-300 hover:bg-slate-700" : "bg-emerald-600 text-white"
                      }`}
                    >
                      {card.is_published ? "Unpublish" : "Publish Now"}
                    </button>

                    <div className="flex gap-2">
                      <button
                        onClick={() => handleOpenEditModal(card)}
                        className="px-3 py-1.5 rounded-xl bg-amber-500 hover:bg-amber-400 text-slate-950 font-bold text-xs flex items-center gap-1"
                      >
                        <FiEdit3 size={13} /> Edit
                      </button>
                      <button
                        onClick={() => handleUnfeature(card)}
                        className="px-3 py-1.5 rounded-xl bg-rose-900/60 hover:bg-rose-800 text-rose-200 font-bold text-xs flex items-center gap-1"
                        title="Unfeature without deleting destination"
                      >
                        <FiTrash2 size={13} /> Unfeature
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}

      {/* CREATE / EDIT FEATURED DESTINATION MODAL */}
      <AnimatePresence>
        {showModal && (
          <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4 backdrop-blur-sm overflow-y-auto">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-slate-950 border border-slate-800 rounded-3xl max-w-2xl w-full p-6 sm:p-8 space-y-6 shadow-2xl text-white my-8 max-h-[90vh] overflow-y-auto"
            >
              <div className="flex justify-between items-start border-b border-slate-800 pb-4">
                <div>
                  <span className="text-[10px] font-black uppercase text-amber-400 tracking-wider">
                    Admin Content Publishing Studio
                  </span>
                  <h3 className="text-2xl font-black mt-1">
                    {editingCard ? `Edit Featured Card #${editingCard.id}` : "Feature a Destination"}
                  </h3>
                  <p className="text-xs text-slate-400">
                    Select an existing destination record and customize its promotional card.
                  </p>
                </div>
                <button
                  onClick={() => setShowModal(false)}
                  className="p-2 rounded-full bg-slate-800 hover:bg-slate-700 text-slate-300"
                >
                  <FiX size={20} />
                </button>
              </div>

              <form onSubmit={handleSave} className="space-y-4 text-xs">
                {/* Destination Selector */}
                {!editingCard && (
                  <div className="space-y-2">
                    <label className="font-bold text-amber-300 block">
                      1. Select Destination from Catalogue *
                    </label>
                    {selectedDest ? (
                      <div className="p-3.5 rounded-2xl bg-amber-950/40 border border-amber-500/40 flex items-center justify-between">
                        <div>
                          <p className="font-black text-sm text-white">{selectedDest.name}</p>
                          <p className="text-[11px] text-amber-200">📍 {selectedDest.city || selectedDest.district}, {selectedDest.province}</p>
                        </div>
                        <button
                          type="button"
                          onClick={() => { setSelectedDest(null); setDestGallery([]) }}
                          className="px-3 py-1 rounded-xl bg-slate-800 text-slate-300 text-xs hover:text-white"
                        >
                          Change
                        </button>
                      </div>
                    ) : (
                      <div className="relative">
                        <input
                          type="text"
                          value={destSearch}
                          onChange={(e) => setDestSearch(e.target.value)}
                          placeholder="Search destination by name or city (e.g., Pokhara, Phewa Lake)..."
                          className="w-full px-4 py-3 rounded-2xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                        />
                        {destResults.length > 0 && (
                          <div className="absolute top-full left-0 right-0 mt-1 rounded-2xl bg-slate-900 border border-slate-700 shadow-2xl z-20 max-h-48 overflow-y-auto divide-y divide-slate-800">
                            {destResults.map((d) => (
                              <button
                                key={d.id}
                                type="button"
                                onClick={() => handleSelectDestination(d)}
                                className="w-full text-left p-3 hover:bg-slate-800 flex justify-between items-center"
                              >
                                <div>
                                  <p className="font-bold text-white">{d.name}</p>
                                  <p className="text-[11px] text-slate-400">{d.city || d.district}, {d.province}</p>
                                </div>
                                <span className="text-[10px] px-2 py-0.5 rounded bg-amber-400/20 text-amber-300 font-bold">Select</span>
                              </button>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Custom Promotional Title */}
                <div className="space-y-1">
                  <label className="font-bold text-slate-300 block">Promotional Title</label>
                  <input
                    type="text"
                    value={form.title}
                    onChange={(e) => setForm({ ...form, title: e.target.value })}
                    placeholder="e.g. Discover the Majestic Pokhara Valley"
                    className="w-full px-4 py-2.5 rounded-2xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                  />
                  <p className="text-[11px] text-slate-500">Leave empty to use the original destination name.</p>
                </div>

                {/* Custom Promotional Description */}
                <div className="space-y-1">
                  <label className="font-bold text-slate-300 block">Promotional Description</label>
                  <textarea
                    rows="3"
                    value={form.short_description}
                    onChange={(e) => setForm({ ...form, short_description: e.target.value })}
                    placeholder="Short summary highlighting why travelers should visit..."
                    className="w-full px-4 py-2.5 rounded-2xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                  />
                </div>

                {/* Media Selection */}
                <div className="space-y-2">
                  <label className="font-bold text-slate-300 block">Featured Image Selection</label>
                  {destGallery.length > 0 && (
                    <div>
                      <p className="text-[11px] text-slate-400 mb-1.5">Pick from verified destination gallery:</p>
                      <div className="grid grid-cols-4 sm:grid-cols-6 gap-2 max-h-32 overflow-y-auto p-2 bg-slate-900 rounded-2xl border border-slate-800">
                        {destGallery.map((img) => {
                          const isSel = form.featured_media_id === img.id
                          const url = img.url || img.external_url || img.image_url
                          return (
                            <button
                              key={img.id}
                              type="button"
                              onClick={() => setForm({ ...form, featured_media_id: img.id, featured_media_url: url })}
                              className={`relative rounded-xl overflow-hidden h-16 border-2 transition-all ${
                                isSel ? "border-amber-400 scale-105" : "border-transparent opacity-60 hover:opacity-100"
                              }`}
                            >
                              <img src={url} alt="Gallery" className="w-full h-full object-cover" />
                              {isSel && <span className="absolute inset-0 bg-amber-400/30 grid place-items-center"><FiCheck className="text-slate-950 font-black" /></span>}
                            </button>
                          )
                        })}
                      </div>
                    </div>
                  )}

                  <div>
                    <label className="text-[11px] text-slate-400 block mb-1">Or direct Image URL override:</label>
                    <input
                      type="text"
                      value={form.featured_media_url}
                      onChange={(e) => setForm({ ...form, featured_media_url: e.target.value })}
                      placeholder="https://images.unsplash.com/..."
                      className="w-full px-4 py-2.5 rounded-2xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                    />
                  </div>
                </div>

                {/* CTA Configuration */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <label className="font-bold text-slate-300 block">Call-to-Action (CTA) Label</label>
                    <input
                      type="text"
                      value={form.cta_label}
                      onChange={(e) => setForm({ ...form, cta_label: e.target.value })}
                      placeholder="e.g. Plan Your Visit"
                      className="w-full px-4 py-2.5 rounded-2xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                    />
                  </div>
                  <div className="space-y-1">
                    <label className="font-bold text-slate-300 block">CTA Route / URL</label>
                    <input
                      type="text"
                      value={form.cta_url}
                      onChange={(e) => setForm({ ...form, cta_url: e.target.value })}
                      placeholder="/destinations/phewa-lake"
                      className="w-full px-4 py-2.5 rounded-2xl bg-slate-900 border border-slate-700 text-white placeholder-slate-500 focus:outline-none focus:border-amber-400"
                    />
                  </div>
                </div>

                {/* Display Order & Publishing Options */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 items-center pt-2 border-t border-slate-800">
                  <div className="space-y-1">
                    <label className="font-bold text-slate-300 block">Display Order Position</label>
                    <input
                      type="number"
                      min="1"
                      value={form.display_order}
                      onChange={(e) => setForm({ ...form, display_order: e.target.value })}
                      className="w-full px-4 py-2.5 rounded-2xl bg-slate-900 border border-slate-700 text-white focus:outline-none focus:border-amber-400"
                    />
                  </div>

                  <div className="space-y-1 pt-4">
                    <label className="inline-flex items-center gap-2 font-bold text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={form.is_published}
                        onChange={(e) => setForm({ ...form, is_published: e.target.checked })}
                        className="w-4 h-4 rounded text-amber-400 focus:ring-amber-400"
                      />
                      <span>Publish immediately to live public site</span>
                    </label>
                  </div>
                </div>

                {/* Live Card Preview */}
                <div className="p-4 rounded-3xl bg-slate-900/80 border border-amber-500/30 space-y-2">
                  <span className="text-[10px] font-black uppercase text-amber-400 block">Live Preview Card</span>
                  <div className="p-4 rounded-2xl bg-white text-slate-900 space-y-2 shadow-lg">
                    <div className="h-32 rounded-xl bg-slate-100 overflow-hidden relative">
                      <img
                        src={form.featured_media_url || selectedDest?.cover_image_url || "/images/destinations/annapurna/img1.jpg"}
                        alt="Preview"
                        className="w-full h-full object-cover"
                      />
                      <span className="absolute bottom-2 left-2 px-2 py-0.5 rounded bg-black/60 text-white text-[10px] font-bold">
                        📍 {selectedDest?.name || "Selected Destination"}
                      </span>
                    </div>
                    <h4 className="font-bold text-sm text-slate-900">{form.title || selectedDest?.name || "Card Title"}</h4>
                    <p className="text-xs text-slate-600 line-clamp-2">{form.short_description || "Promotional card description..."}</p>
                    <button type="button" className="px-3 py-1.5 rounded-xl bg-[#102A2E] text-white text-xs font-bold">
                      {form.cta_label || "Explore Destination"} →
                    </button>
                  </div>
                </div>

                {/* Submit Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t border-slate-800">
                  <button
                    type="button"
                    onClick={() => setShowModal(false)}
                    className="px-5 py-2.5 rounded-2xl bg-slate-800 hover:bg-slate-700 text-slate-300 font-bold"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-6 py-2.5 rounded-2xl bg-amber-400 hover:bg-amber-500 text-slate-950 font-black shadow-lg shadow-amber-400/20"
                  >
                    {editingCard ? "Save Changes" : "Publish Featured Card"}
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
