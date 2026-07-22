// CONFIRMED WORKING as-is — matches POST /destinations/ (multipart) exactly.
import React, { useState } from "react";
import { destinationApi, getCurrentPosition } from "../services/api.js";

/**
 * Demonstrates a tourist submitting a new place WITH an image in a single
 * multipart/form-data request. The backend marks it "pending" and hides it
 * from the public list until an admin approves it (see approve() in api.js
 * / the DestinationViewSet.approve action on the backend).
 */
export default function SubmitPlacePage() {
  const [form, setForm] = useState({ name: "", category: 1, description: "" });
  const [image, setImage] = useState(null);
  const [status, setStatus] = useState(null);

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
      await destinationApi.submit(formData);
      setStatus("Submitted! An admin will review it before it appears publicly.");
    } catch (err) {
      setStatus(
        err.response?.status === 401
          ? "You need to log in first."
          : JSON.stringify(err.response?.data || "Submission failed.")
      );
    }
  }

  return (
    <div className="card">
      <h3>Submit a Place</h3>
      <form onSubmit={handleSubmit}>
        <input placeholder="Place name" value={form.name} onChange={(e) => update("name", e.target.value)} required />
        <input
          type="number"
          placeholder="Category ID"
          value={form.category}
          onChange={(e) => update("category", e.target.value)}
          required
        />
        <textarea
          placeholder="Description"
          value={form.description}
          onChange={(e) => update("description", e.target.value)}
          required
        />
        <input type="file" accept="image/*" onChange={(e) => setImage(e.target.files[0])} />
        <button type="submit">Submit Place</button>
      </form>
      {status && <p>{status}</p>}
    </div>
  );
}