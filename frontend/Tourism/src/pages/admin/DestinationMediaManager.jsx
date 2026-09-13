import { useEffect, useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { FiImage, FiTrash2, FiPlus, FiClock, FiExternalLink, FiCheck, FiX, FiMapPin, FiClipboard, FiTag } from "react-icons/fi"
import destinationApi from "../../api/destinationApi"
import adminPanelApi from "../../api/adminPanelApi"
import Loader from "../../components/common/Loader"
import EmptyState from "../../components/common/EmptyState"
import useToast from "../../hooks/useToast"

/**
 * DestinationMediaManager
 *
 * Real, working admin feature — add images to a destination, view its
 * current gallery and delete photos, and view its moderation history.
 * Uses the endpoints added in tourist/views.py (photos GET/POST/DELETE,
 * history GET) and admin_panel/views.py (destinations-missing-images).
 *
 * Left column: destinations missing images (the actual to-do list —
 * excludes hotels/guesthouses/etc, confirmed live against the real
 * database that ~61% of "destination" rows are actually miscategorized
 * accommodation listings, not real places).
 * Right column: selected destination's gallery + add-photo form +
 * audit history.
 */
const DestinationMediaManager = () => {
  const [queue, setQueue] = useState([])
  const [loadingQueue, setLoadingQueue] = useState(true)
  const [page, setPage] = useState(1)
  const [hasNext, setHasNext] = useState(false)
  const [totalMissing, setTotalMissing] = useState(null)

  const [selected, setSelected] = useState(null) // { id, name, slug, ... }
  const [photos, setPhotos] = useState([])
  const [history, setHistory] = useState([])
  const [loadingDetail, setLoadingDetail] = useState(false)

  // ADDED -- lets staff open ANY destination to preview/manage its
  // existing photos, not just ones in the "missing images" queue on
  // the left (that list only ever shows destinations with zero
  // images -- there was previously no way to browse to a destination
  // that already has photos to review or replace them).
  const [searchQuery, setSearchQuery] = useState("")
  const [searchResults, setSearchResults] = useState([])
  const [searching, setSearching] = useState(false)

  const [form, setForm] = useState({ externalUrl: "", caption: "", isCover: true })
  const [submitting, setSubmitting] = useState(false)
  const [deletingId, setDeletingId] = useState(null)

  // ADDED -- image preview state for the "Add a photo" form. Was
  // previously a plain text input: an admin could paste a broken URL,
  // the wrong image, or a non-image link entirely and only find out
  // after it was already saved to the gallery. Now the pasted URL is
  // rendered live so the admin sees exactly what they're about to add
  // before committing it, with clear ok/broken feedback.
  const [previewStatus, setPreviewStatus] = useState("idle") // idle | loading | ok | error

  // ADDED -- "Add Destination" form. Reuses the same real submission
  // endpoint tourists use (SubmitPlacePage.jsx / POST /destinations/),
  // but with EXPLICIT latitude/longitude number fields instead of
  // auto-detected browser geolocation -- that's right for a tourist
  // submitting "I'm standing here, this is a hidden gem", but wrong
  // for an admin who knows a real place's exact researched coordinates
  // and isn't physically there. Staff submissions auto-publish
  // immediately (see DestinationWriteSerializer.create()).
  const [showAddForm, setShowAddForm] = useState(false)
  const [categories, setCategories] = useState([])
  const [addForm, setAddForm] = useState({
    name: "", category: "", description: "", short_description: "",
    latitude: "", longitude: "", district: "", province: "",
    best_time_to_visit: "", history: "",
  })
  const [addSubmitting, setAddSubmitting] = useState(false)

  // ADDED -- "Manage Categories" panel: add new ones, delete unused
  // ones. Reuses the same `categories` list the destination form's
  // dropdown already loads.
  const [showCategoryForm, setShowCategoryForm] = useState(false)
  const [newCategory, setNewCategory] = useState({ name: "", description: "" })
  const [categorySubmitting, setCategorySubmitting] = useState(false)
  const [deletingCategoryId, setDeletingCategoryId] = useState(null)

  const loadCategories = () =>
    destinationApi
      // FIXED: this had no page_size, so it silently only ever loaded
      // the first page (10 of 47 categories) -- the "Add Destination"
      // category dropdown above was missing 37 real categories,
      // confirmed against the live API while building category
      // management.
      .getCategories({ page_size: 200 })
      .then(({ data }) => setCategories(data.results || data || []))
      .catch(() => setCategories([]))

  useEffect(() => {
    loadCategories()
  }, [])

  const handleCreateCategory = async (e) => {
    e.preventDefault()
    if (!newCategory.name.trim()) return
    setCategorySubmitting(true)
    try {
      await destinationApi.createCategory(newCategory)
      showToast(`Category "${newCategory.name}" added.`, "success")
      setNewCategory({ name: "", description: "" })
      loadCategories()
    } catch (err) {
      showToast(err.response?.data?.name?.[0] || "Could not create category.", "error")
    } finally {
      setCategorySubmitting(false)
    }
  }

  const handleDeleteCategory = async (cat) => {
    if (cat.destination_count > 0) {
      showToast(`Can't delete — ${cat.destination_count} destination(s) still use this category.`, "error")
      return
    }
    setDeletingCategoryId(cat.id)
    try {
      await destinationApi.deleteCategory(cat.slug)
      setCategories((prev) => prev.filter((c) => c.id !== cat.id))
      showToast("Category deleted.", "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not delete category.", "error")
    } finally {
      setDeletingCategoryId(null)
    }
  }

  const updateAddForm = (field, value) => setAddForm((f) => ({ ...f, [field]: value }))

  const resetAddForm = () =>
    setAddForm({
      name: "", category: "", description: "", short_description: "",
      latitude: "", longitude: "", district: "", province: "",
      best_time_to_visit: "", history: "",
    })

  const handleCreateDestination = async (e) => {
    e.preventDefault()
    setAddSubmitting(true)
    try {
      const { data } = await destinationApi.create(addForm)
      showToast(`"${data.name}" published.`, "success")
      resetAddForm()
      setShowAddForm(false)
      // Jump straight into managing its photos -- it has none yet.
      openDestination({ id: data.id, slug: data.slug || addForm.name, name: data.name, city: addForm.district })
      loadQueue(page)
    } catch (err) {
      const errors = err.response?.data
      const firstError = errors && typeof errors === "object"
        ? Object.values(errors).flat()[0]
        : "Could not create destination."
      showToast(firstError || "Could not create destination.", "error")
    } finally {
      setAddSubmitting(false)
    }
  }

  const { showToast } = useToast()

  const loadQueue = (pageNum = 1) => {
    setLoadingQueue(true)
    adminPanelApi
      .getDestinationsMissingImages(pageNum)
      .then(({ data }) => {
        setQueue(data.results || [])
        setHasNext(!!data.next)
        setTotalMissing(data.count ?? null)
        setPage(pageNum)
      })
      .catch(() =>
        showToast("Could not load the missing-images queue — admin access required.", "error")
      )
      .finally(() => setLoadingQueue(false))
  }

  useEffect(loadQueue, [])

  // Debounced destination search — searches ALL destinations (not just
  // the missing-images queue), so staff can find and preview a place
  // that already has photos.
  const debouncedQuery = searchQuery.trim()
  const [prevQuery, setPrevQuery] = useState(debouncedQuery)
  if (prevQuery !== debouncedQuery) {
    setPrevQuery(debouncedQuery)
    if (debouncedQuery.length < 2) {
      setSearchResults([])
      setSearching(false)
    } else {
      setSearching(true)
    }
  }

  useEffect(() => {
    const query = debouncedQuery
    if (query.length < 2) {
      return
    }
    const timeout = setTimeout(() => {
      destinationApi
        .search(query)
        .then(({ data }) => setSearchResults(data || []))
        .catch(() => setSearchResults([]))
        .finally(() => setSearching(false))
    }, 300)
    return () => clearTimeout(timeout)
  }, [debouncedQuery])

  const openDestination = (dest) => {
    setSelected(dest)
    setForm({ externalUrl: "", caption: "", isCover: true })
    setPreviewStatus("idle")
    setLoadingDetail(true)
    Promise.all([
      destinationApi.getPhotos(dest.slug),
      destinationApi.getHistory(dest.slug).catch(() => ({ data: { history: [] } })),
    ])
      .then(([photosRes, historyRes]) => {
        setPhotos(photosRes.data.photos || [])
        setHistory(historyRes.data.history || [])
      })
      .catch(() => showToast("Could not load that destination's media.", "error"))
      .finally(() => setLoadingDetail(false))
  }

  const handleAddPhoto = async (e) => {
    e.preventDefault()
    if (!selected || !form.externalUrl.trim()) return
    if (previewStatus === "error") {
      showToast("That image URL doesn't load — fix it before adding.", "error")
      return
    }
    setSubmitting(true)
    try {
      const { data } = await destinationApi.addPhoto(selected.slug, form)
      setPhotos((prev) => [data, ...prev])
      setForm({ externalUrl: "", caption: "", isCover: false })
      setPreviewStatus("idle")
      showToast("Photo added.", "success")
      // This destination now has an image — drop it from the queue.
      setQueue((prev) => prev.filter((d) => d.id !== selected.id))
    } catch (err) {
      showToast(err.response?.data?.detail || err.response?.data?.external_url?.[0] || "Could not add photo.", "error")
    } finally {
      setSubmitting(false)
    }
  }

  const handleDeletePhoto = async (photoId) => {
    if (!selected) return
    setDeletingId(photoId)
    try {
      await destinationApi.deletePhoto(selected.slug, photoId)
      setPhotos((prev) => prev.filter((p) => p.id !== photoId))
      showToast("Photo removed.", "success")
    } catch (err) {
      showToast(err.response?.data?.detail || "Could not remove photo.", "error")
    } finally {
      setDeletingId(null)
    }
  }

  return (
    <div className="container-app py-10 fade-in">
      <div className="flex items-start justify-between gap-4 mb-1">
        <h1 className="section-title">Destination Media Manager</h1>
        <div className="flex gap-2 shrink-0">
          <button
            onClick={() => setShowCategoryForm((s) => !s)}
            className="btn-outline text-sm py-2 px-4 flex items-center gap-2"
          >
            <FiClipboard size={14} /> {showCategoryForm ? "Close" : "Categories"}
          </button>
          <button
            onClick={() => setShowAddForm((s) => !s)}
            className="btn-primary text-sm py-2 px-4 flex items-center gap-2"
          >
            <FiMapPin size={14} /> {showAddForm ? "Cancel" : "Add Destination"}
          </button>
        </div>
      </div>
      <p className="text-gray-500 text-sm mb-6">
        Add real photos to destinations, review what's already there, and check a destination's moderation history.
        {totalMissing !== null && (
          <> Queue excludes hotels/guesthouses/etc — <strong>{totalMissing}</strong> genuine destinations still need photos.</>
        )}
      </p>

      {/* Add Destination form -- collapsed by default */}
      <AnimatePresence>
        {showAddForm && (
          <motion.form
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            onSubmit={handleCreateDestination}
            className="card-base p-6 mb-6 overflow-hidden"
          >
            <h2 className="font-semibold mb-1 flex items-center gap-2">
              <FiMapPin className="text-himalaya-500" /> Add a new destination
            </h2>
            <p className="text-xs text-gray-400 mb-4">
              Goes live immediately (staff submissions don't need approval) — enter the real coordinates, not your own location.
            </p>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-gray-500">Place Name</label>
                <input
                  required
                  className="input-field mt-1"
                  placeholder="e.g. Rara Lake"
                  value={addForm.name}
                  onChange={(e) => updateAddForm("name", e.target.value)}
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-500">Category</label>
                <select
                  required
                  className="input-field mt-1"
                  value={addForm.category}
                  onChange={(e) => updateAddForm("category", e.target.value)}
                >
                  <option value="" disabled>Select a category</option>
                  {categories.map((cat) => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>

              <div />

              <div>
                <label className="text-xs font-medium text-gray-500">Latitude</label>
                <input
                  required
                  type="number"
                  step="any"
                  placeholder="e.g. 29.5330"
                  className="input-field mt-1"
                  value={addForm.latitude}
                  onChange={(e) => updateAddForm("latitude", e.target.value)}
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-500">Longitude</label>
                <input
                  required
                  type="number"
                  step="any"
                  placeholder="e.g. 82.0800"
                  className="input-field mt-1"
                  value={addForm.longitude}
                  onChange={(e) => updateAddForm("longitude", e.target.value)}
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-500">District</label>
                <input
                  className="input-field mt-1"
                  placeholder="e.g. Mugu"
                  value={addForm.district}
                  onChange={(e) => updateAddForm("district", e.target.value)}
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-500">Province</label>
                <input
                  className="input-field mt-1"
                  placeholder="e.g. Karnali Province"
                  value={addForm.province}
                  onChange={(e) => updateAddForm("province", e.target.value)}
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-gray-500">Short Description</label>
                <input
                  className="input-field mt-1"
                  placeholder="One line for cards/previews"
                  value={addForm.short_description}
                  onChange={(e) => updateAddForm("short_description", e.target.value)}
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-gray-500">Description</label>
                <textarea
                  required
                  rows={3}
                  className="input-field mt-1"
                  placeholder="What makes this place worth visiting?"
                  value={addForm.description}
                  onChange={(e) => updateAddForm("description", e.target.value)}
                />
              </div>

              <div>
                <label className="text-xs font-medium text-gray-500">Best Time to Visit</label>
                <input
                  className="input-field mt-1"
                  placeholder="e.g. October to April"
                  value={addForm.best_time_to_visit}
                  onChange={(e) => updateAddForm("best_time_to_visit", e.target.value)}
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-xs font-medium text-gray-500">History</label>
                <textarea
                  rows={2}
                  className="input-field mt-1"
                  placeholder="Historical background, shown on the detail page"
                  value={addForm.history}
                  onChange={(e) => updateAddForm("history", e.target.value)}
                />
              </div>
            </div>

            <button type="submit" disabled={addSubmitting} className="btn-primary text-sm py-2 mt-4">
              {addSubmitting ? "Publishing..." : "Publish Destination"}
            </button>
          </motion.form>
        )}
      </AnimatePresence>

      {/* Manage Categories panel */}
      <AnimatePresence>
        {showCategoryForm && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="card-base p-6 mb-6 overflow-hidden"
          >
            <h2 className="font-semibold mb-1 flex items-center gap-2">
              <FiTag className="text-himalaya-500" /> Manage Categories
            </h2>
            <p className="text-xs text-gray-400 mb-4">
              These populate the category dropdown when adding a destination, and are used for browsing/filtering across the site.
            </p>

            <form onSubmit={handleCreateCategory} className="flex flex-col sm:flex-row gap-2 mb-4">
              <input
                required
                placeholder="New category name (e.g. Hiking)"
                className="input-field flex-1"
                value={newCategory.name}
                onChange={(e) => setNewCategory((c) => ({ ...c, name: e.target.value }))}
              />
              <input
                placeholder="Description (optional)"
                className="input-field flex-1"
                value={newCategory.description}
                onChange={(e) => setNewCategory((c) => ({ ...c, description: e.target.value }))}
              />
              <button type="submit" disabled={categorySubmitting} className="btn-primary text-sm px-4 shrink-0">
                {categorySubmitting ? "Adding..." : "Add"}
              </button>
            </form>

            <div className="max-h-64 overflow-y-auto border border-gray-100 rounded-lg divide-y divide-gray-50">
              {categories.length === 0 ? (
                <p className="text-xs text-gray-400 px-3 py-2">No categories yet.</p>
              ) : (
                categories.map((cat) => (
                  <div key={cat.id} className="flex items-center justify-between px-3 py-2 text-sm">
                    <div className="min-w-0">
                      <span className="font-medium">{cat.name}</span>
                      <span className="text-xs text-gray-400 ml-2">
                        {cat.destination_count} destination{cat.destination_count === 1 ? "" : "s"}
                      </span>
                    </div>
                    <button
                      onClick={() => handleDeleteCategory(cat)}
                      disabled={deletingCategoryId === cat.id}
                      className="text-gray-300 hover:text-nepalred-500 transition-colors shrink-0 ml-2"
                      title={cat.destination_count > 0 ? "In use — can't delete" : "Delete category"}
                    >
                      <FiTrash2 size={14} />
                    </button>
                  </div>
                ))
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
        {/* Queue + search */}
        <div className="card-base p-4">
          {/* ADDED -- search ANY destination, not just the missing-images
              queue below, so staff can preview/manage photos on a place
              that already has some. */}
          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <FiMapPin className="text-himalaya-500" /> Find a destination
          </h2>
          <input
            type="text"
            placeholder="Search any destination by name..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 mb-2 focus:outline-none focus:ring-2 focus:ring-himalaya-500"
          />
          {searchQuery.trim().length >= 2 && (
            <div className="mb-4 max-h-48 overflow-y-auto border border-gray-100 rounded-lg divide-y divide-gray-50">
              {searching ? (
                <p className="text-xs text-gray-400 px-3 py-2">Searching...</p>
              ) : searchResults.length === 0 ? (
                <p className="text-xs text-gray-400 px-3 py-2">No matches.</p>
              ) : (
                searchResults.map((dest) => (
                  <button
                    key={dest.id}
                    onClick={() => {
                      openDestination(dest)
                      setSearchQuery("")
                      setSearchResults([])
                    }}
                    className={`w-full text-left px-3 py-2 text-sm hover:bg-gray-50 ${
                      selected?.id === dest.id ? "bg-himalaya-50 text-himalaya-700 font-medium" : ""
                    }`}
                  >
                    {dest.name}
                    {dest.city && <span className="text-gray-400"> — {dest.city}</span>}
                  </button>
                ))
              )}
            </div>
          )}

          <h2 className="font-semibold mb-3 flex items-center gap-2">
            <FiImage className="text-himalaya-500" /> Needs photos
          </h2>

          {loadingQueue ? (
            <Loader />
          ) : queue.length === 0 ? (
            <EmptyState title="Nothing in the queue" subtitle="Every genuine destination has at least one photo." />
          ) : (
            <>
              <div className="space-y-1 max-h-[60vh] overflow-y-auto">
                {queue.map((dest) => (
                  <button
                    key={dest.id}
                    onClick={() => openDestination(dest)}
                    className={`w-full text-left px-3 py-2 rounded-lg text-sm transition-colors ${
                      selected?.id === dest.id ? "bg-himalaya-50 text-himalaya-700 font-medium" : "hover:bg-gray-50"
                    }`}
                  >
                    {dest.name}
                    {dest.city && <span className="text-gray-400"> — {dest.city}</span>}
                  </button>
                ))}
              </div>

              {(page > 1 || hasNext) && (
                <div className="flex justify-between mt-3 text-sm">
                  <button
                    disabled={page <= 1}
                    onClick={() => loadQueue(page - 1)}
                    className="text-himalaya-600 disabled:text-gray-300"
                  >
                    ← Prev
                  </button>
                  <button
                    disabled={!hasNext}
                    onClick={() => loadQueue(page + 1)}
                    className="text-himalaya-600 disabled:text-gray-300"
                  >
                    Next →
                  </button>
                </div>
              )}
            </>
          )}
        </div>

        {/* Detail */}
        <div className="card-base p-6">
          {!selected ? (
            <EmptyState title="Pick a destination" subtitle="Select one from the queue on the left to manage its photos." />
          ) : loadingDetail ? (
            <Loader />
          ) : (
            <>
              <h2 className="text-xl font-semibold mb-1">{selected.name}</h2>
              <p className="text-sm text-gray-400 mb-6">
                {selected.city || selected.district || "No location on file"}
              </p>

              {/* Add photo */}
              <form onSubmit={handleAddPhoto} className="mb-8 space-y-3">
                <h3 className="font-medium flex items-center gap-2">
                  <FiPlus className="text-himalaya-500" /> Add a photo
                </h3>
                <input
                  type="url"
                  required
                  placeholder="https://commons.wikimedia.org/wiki/Special:FilePath/..."
                  value={form.externalUrl}
                  onChange={(e) => {
                    const url = e.target.value
                    setForm((f) => ({ ...f, externalUrl: url }))
                    setPreviewStatus(url.trim() ? "loading" : "idle")
                  }}
                  className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-himalaya-500"
                />

                {/* ADDED: live preview -- shows exactly what's about to
                    be added, before it's saved. */}
                {form.externalUrl.trim() && (
                  <div className="rounded-lg border border-gray-200 overflow-hidden bg-gray-50">
                    {previewStatus === "error" ? (
                      <div className="h-40 flex flex-col items-center justify-center gap-1.5 text-red-500 text-sm">
                        <FiX size={20} />
                        This URL doesn't load as an image
                      </div>
                    ) : (
                      <div className="relative h-40">
                        {previewStatus === "loading" && (
                          <div className="absolute inset-0 flex items-center justify-center text-xs text-gray-400">
                            Loading preview...
                          </div>
                        )}
                        <img
                          src={form.externalUrl}
                          alt="Preview"
                          className={`w-full h-40 object-cover ${previewStatus === "ok" ? "" : "opacity-0"}`}
                          onLoad={() => setPreviewStatus("ok")}
                          onError={() => setPreviewStatus("error")}
                        />
                      </div>
                    )}
                  </div>
                )}
                <input
                  type="text"
                  placeholder="Caption (optional)"
                  value={form.caption}
                  onChange={(e) => setForm((f) => ({ ...f, caption: e.target.value }))}
                  className="w-full text-sm rounded-lg border border-gray-200 px-3 py-2 focus:outline-none focus:ring-2 focus:ring-himalaya-500"
                />
                <label className="flex items-center gap-2 text-sm text-gray-600">
                  <input
                    type="checkbox"
                    checked={form.isCover}
                    onChange={(e) => setForm((f) => ({ ...f, isCover: e.target.checked }))}
                  />
                  Set as cover photo
                </label>
                <button
                  type="submit"
                  disabled={submitting || previewStatus === "error" || previewStatus === "loading"}
                  className="btn-primary text-sm py-2 disabled:opacity-50"
                >
                  {submitting ? "Adding..." : "Add photo"}
                </button>
              </form>

              {/* Gallery */}
              <h3 className="font-medium mb-3">Current gallery ({photos.length})</h3>
              {photos.length === 0 ? (
                <p className="text-sm text-gray-400 mb-8">No photos yet.</p>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-8">
                  <AnimatePresence>
                    {photos.map((p) => (
                      <motion.div
                        key={p.id}
                        initial={{ opacity: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        className="relative group rounded-lg overflow-hidden border border-gray-100"
                      >
                        <img src={p.display_url} alt={p.caption} className="w-full h-28 object-cover" />
                        {p.is_cover && (
                          <span className="absolute top-1 left-1 bg-himalaya-500 text-white text-[10px] px-1.5 py-0.5 rounded">
                            Cover
                          </span>
                        )}
                        <button
                          onClick={() => handleDeletePhoto(p.id)}
                          disabled={deletingId === p.id}
                          className="absolute top-1 right-1 bg-black/60 text-white p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Remove photo"
                        >
                          <FiTrash2 size={12} />
                        </button>
                      </motion.div>
                    ))}
                  </AnimatePresence>
                </div>
              )}

              {/* History */}
              <h3 className="font-medium mb-3 flex items-center gap-2">
                <FiClock className="text-himalaya-500" /> History
              </h3>
              {history.length === 0 ? (
                <p className="text-sm text-gray-400">No moderation history recorded.</p>
              ) : (
                <ul className="space-y-2 text-sm">
                  {history.map((h) => (
                    <li key={h.id} className="flex items-start gap-2 text-gray-600">
                      {h.action === "approved" ? (
                        <FiCheck className="text-green-500 mt-0.5 shrink-0" />
                      ) : h.action === "rejected" ? (
                        <FiX className="text-red-500 mt-0.5 shrink-0" />
                      ) : (
                        <FiExternalLink className="text-gray-400 mt-0.5 shrink-0" />
                      )}
                      <span>
                        <span className="font-medium capitalize">{h.action}</span>
                        {h.actor && <> by {h.actor}</>} — {new Date(h.created_at).toLocaleDateString()}
                        {h.note && <span className="text-gray-400"> ({h.note})</span>}
                      </span>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default DestinationMediaManager 