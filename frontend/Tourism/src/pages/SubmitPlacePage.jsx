import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { FiMapPin, FiUploadCloud } from "react-icons/fi";
import { destinationApi as legacyDestinationApi, getCurrentPosition } from "../services/api.js";
import destinationApi from "../api/destinationApi";

/**
 * Lets a tourist submit a new place with an image in a single
 * multipart/form-data request. The backend marks it "pending" and hides
 * it from the public list until an admin approves it (see approve() in
 * services/api.js / the DestinationViewSet.approve action).
 *
 * FIXED: this page previously had no route anywhere in App.jsx — it was
 * fully built and working but completely unreachable. Also replaced the
 * raw "Category ID" number input (which required the submitter to know
 * a numeric database ID by memory) with a real dropdown populated from
 * destinationApi.getCategories().
 */
export default function SubmitPlacePage() {
  const [form, setForm] = useState({ name: "", category: "", description: "" });
  const [image, setImage] = useState(null);
  const [status, setStatus] = useState(null);
  const [categories, setCategories] = useState([]);

  useEffect(() => {
    destinationApi
      .getCategories()
      .then(({ data }) => setCategories(data.results || data || []))
      .catch(() => setCategories([]));
  }, []);

  function update(field, value) {
    setForm((prev) => ({ ...prev, [field]: value }));
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus("Getting your location...");
    const coords = (await getCurrentPosition()) || { latitude: 28.2096, longitude: 83.9856 };

    const formData = new FormData();
    formData.append("name", form.name);
    formData.append("category", form.category);
    formData.append("description", form.description);
    formData.append("latitude", coords.latitude);
    formData.append("longitude", coords.longitude);
    if (image) formData.append("cover_image", image);

    setStatus("Submitting...");
    try {
      await legacyDestinationApi.submit(formData);
      setStatus("Submitted! An admin will review it before it appears publicly.");
      setForm({ name: "", category: "", description: "" });
      setImage(null);
    } catch (err) {
      setStatus(
        err.response?.status === 401
          ? "You need to log in first."
          : JSON.stringify(err.response?.data || "Submission failed.")
      );
    }
  }

  return (
    <div className="container-app py-10 fade-in max-w-xl">
      <h1 className="section-title flex items-center gap-2">
        <FiMapPin className="text-himalaya-500" /> Submit a Place
      </h1>
      <p className="text-gray-500 text-sm mb-6">
        Know a hidden gem? Submit it here — an admin will review it before it goes live.
      </p>

      <motion.form
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        onSubmit={handleSubmit}
        className="card-base p-6 space-y-4"
      >
        <div>
          <label className="text-xs font-medium text-gray-500">Place Name</label>
          <input
            className="input-field mt-1"
            placeholder="e.g. Hidden waterfall near Bandipur"
            value={form.name}
            onChange={(e) => update("name", e.target.value)}
            required
          />
        </div>

        <div>
          <label className="text-xs font-medium text-gray-500">Category</label>
          <select
            className="input-field mt-1"
            value={form.category}
            onChange={(e) => update("category", e.target.value)}
            required
          >
            <option value="" disabled>Select a category</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>{cat.name}</option>
            ))}
          </select>
        </div>

        <div>
          <label className="text-xs font-medium text-gray-500">Description</label>
          <textarea
            rows={4}
            className="input-field mt-1"
            placeholder="What makes this place worth visiting?"
            value={form.description}
            onChange={(e) => update("description", e.target.value)}
            required
          />
        </div>

        <div>
          <label className="text-xs font-medium text-gray-500 flex items-center gap-1">
            <FiUploadCloud size={12} /> Photo
          </label>
          <input
            type="file"
            accept="image/*"
            className="mt-1 text-sm"
            onChange={(e) => setImage(e.target.files[0])}
          />
        </div>

        <p className="text-xs text-gray-400">
          Your current location will be attached automatically — allow location access when prompted.
        </p>

        <button type="submit" className="btn-primary w-full">Submit Place</button>

        {status && (
          <p className="text-sm bg-himalaya-50 border border-himalaya-100 rounded-lg px-3 py-2 text-himalaya-700">
            {status}
          </p>
        )}
      </motion.form>
    </div>
  );
}