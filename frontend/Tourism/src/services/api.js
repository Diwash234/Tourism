/**
 * Central place where the frontend talks to the Django backend.
 * Every other component/page should import from here rather than calling
 * axios/fetch directly, so the JWT + refresh logic only lives in one spot.
 *
 * Backend base URL comes from VITE_API_BASE_URL (see .env.example) and
 * points at Django's /api/v1/ router (tourist/urls.py).
 */
import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

const api = axios.create({ baseURL: API_BASE_URL });

// --- Attach the JWT access token to every request ---------------------
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("access");
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// --- On a 401, try refreshing the access token once, then retry -------
let isRefreshing = false;
let pendingQueue = [];

function resolvePending(token) {
  pendingQueue.forEach(({ resolve }) => resolve(token));
  pendingQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status !== 401 || original._retry) {
      return Promise.reject(error);
    }

    if (isRefreshing) {
      // Queue this request until the in-flight refresh finishes.
      return new Promise((resolve) => {
        pendingQueue.push({ resolve });
      }).then((token) => {
        original.headers.Authorization = `Bearer ${token}`;
        return api(original);
      });
    }

    original._retry = true;
    isRefreshing = true;
    try {
      const refresh = localStorage.getItem("refresh");
      const { data } = await axios.post(`${API_BASE_URL}/auth/token/refresh/`, { refresh });
      localStorage.setItem("access", data.access);
      resolvePending(data.access);
      original.headers.Authorization = `Bearer ${data.access}`;
      return api(original);
    } catch (refreshError) {
      localStorage.removeItem("access");
      localStorage.removeItem("refresh");
      window.location.href = "/login";
      return Promise.reject(refreshError);
    } finally {
      isRefreshing = false;
    }
  }
);

// ------------------------------------------------------------------
// Auth
// ------------------------------------------------------------------
export const authApi = {
  register: (payload) => api.post("/auth/register/", payload),
  login: async (email, password) => {
    const { data } = await api.post("/auth/login/", { email, password });
    localStorage.setItem("access", data.access);
    localStorage.setItem("refresh", data.refresh);
    return data;
  },
  logout: async () => {
    const refresh = localStorage.getItem("refresh");
    await api.post("/auth/logout/", { refresh });
    localStorage.removeItem("access");
    localStorage.removeItem("refresh");
  },
  verifyEmail: (token) => api.post("/auth/verify-email/", { token }),
  forgotPassword: (email) => api.post("/auth/forgot-password/", { email }),
  resetPassword: (token, new_password) => api.post("/auth/reset-password/", { token, new_password }),
  getProfile: () => api.get("/auth/profile/"),
  updateProfile: (payload) => api.patch("/auth/profile/", payload),
  // Sends the browser's GPS coordinates to the backend; falls back to
  // server-side GeoIP automatically if called with no body.
  updateLocation: (latitude, longitude) => api.post("/auth/update-location/", { latitude, longitude }),
};

// ------------------------------------------------------------------
// Geolocation helper: browser GPS first, GeoIP fallback second
// (mirrors the backend's resolve_location() strategy)
// ------------------------------------------------------------------
export function getCurrentPosition() {
  return new Promise((resolve) => {
    if (!navigator.geolocation) {
      resolve(null); // let the backend fall back to GeoIP
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (pos) => resolve({ latitude: pos.coords.latitude, longitude: pos.coords.longitude }),
      () => resolve(null), // permission denied / unavailable -> GeoIP fallback
      { enableHighAccuracy: true, timeout: 5000 }
    );
  });
}

export async function syncUserLocation() {
  const gps = await getCurrentPosition();
  const { data } = await authApi.updateLocation(gps?.latitude, gps?.longitude);
  return data; // { latitude, longitude, city, country, location_source: "gps"|"geoip", ... }
}

// ------------------------------------------------------------------
// Destinations
// ------------------------------------------------------------------
export const destinationApi = {
  list: (params) => api.get("/destinations/", { params }),
  get: (slug, params) => api.get(`/destinations/${slug}/`, { params }),

  // Text search — same endpoint as list(), just with a `search` param.
  // Combine with photoApi.get(slug) per result to show images inline.
  search: (query, params) => api.get("/destinations/", { params: { search: query, ...params } }),

  // Nearest-first search around a lat/lon, with distance_km on each result.
  nearby: (latitude, longitude, radius_km = 10) =>
    api.get("/destinations/nearby/", { params: { latitude, longitude, radius_km } }),

  // Tourist place submission — multipart because of the cover_image file.
  // Backend marks it "pending" until an admin approves it.
  submit: (formData) =>
    api.post("/destinations/", formData, { headers: { "Content-Type": "multipart/form-data" } }),

  mySubmissions: () => api.get("/destinations/my_submissions/"),
  approve: (slug, status, review_note = "") => api.post(`/destinations/${slug}/approve/`, { status, review_note }),
  translate: (slug, language_code) => api.post(`/destinations/${slug}/translate/`, { language_code }),
};

export const reviewApi = {
  list: (destinationId) => api.get("/reviews/", { params: { destination: destinationId } }),
  create: (destination, comment) => api.post("/reviews/", { destination, comment }),
};

export const ratingApi = {
  create: (destination, value) => api.post("/ratings/", { destination, value }),
};

export const favoriteApi = {
  list: () => api.get("/favorites/"),
  add: (destination) => api.post("/favorites/", { destination }),
  remove: (id) => api.delete(`/favorites/${id}/`),
};

export const historyApi = {
  list: () => api.get("/history/"),
  remove: (id) => api.delete(`/history/${id}/`),
};

export const alertApi = {
  nearby: (latitude, longitude, radius_km = 25) =>
    api.get("/alerts/nearby/", { params: { latitude, longitude, radius_km } }),
};

export const emergencyApi = {
  nearest: (latitude, longitude, radius_km = 25, contact_type) =>
    api.get("/emergency-contacts/nearest/", { params: { latitude, longitude, radius_km, contact_type } }),
};

export const notificationApi = {
  list: () => api.get("/notifications/"),
  markRead: (id) => api.post(`/notifications/${id}/mark_read/`),
  markAllRead: () => api.post("/notifications/mark_all_read/"),
};

// ------------------------------------------------------------------
// Photos: gallery + community upload ("local people can add photos of
// places"). See tourist/views.py::DestinationViewSet.photos and
// utils.py::maybe_promote_photo for the popularity-based auto-promotion
// this powers ("if it's highly searched, it becomes the destination's
// cover photo").
// ------------------------------------------------------------------
export const photoApi = {
  // { photos: [...], external_fallback: {url, attribution, source_link} | null }
  get: (slug) => api.get(`/destinations/${slug}/photos/`),
  upload: (slug, formData) =>
    api.post(`/destinations/${slug}/photos/`, formData, { headers: { "Content-Type": "multipart/form-data" } }),
};

export const hotelApi = {
  list: (destinationId) => api.get("/hotels/", { params: { destination: destinationId } }),
};

export const weatherApi = {
  get: (slug) => api.get(`/destinations/${slug}/weather/`),
};

export const osmApi = {
  nearby: (latitude, longitude, radius_m = 2000) =>
    api.get("/places/osm-nearby/", { params: { latitude, longitude, radius_m } }),
};

// Generic text translation (used by translation.jsx for arbitrary text,
// as opposed to destinationApi.translate() which translates a specific
// destination's stored description/name).
export const translateApi = {
  text: (text, target_language, source_language = "auto") =>
    api.post("/translate/", { text, target_language, source_language }),
};

// ------------------------------------------------------------------
// ML-powered recommendations, safety score, and budget estimate
// (backend proxies each of these to the ML microservice)
// ------------------------------------------------------------------
export const mlApi = {
  recommendations: (latitude, longitude, top_n = 5) =>
    api.post("/ml/recommendations/", { latitude, longitude, top_n }),

  // Pass a destination id, OR raw latitude/longitude.
  safety: ({ destination, latitude, longitude }) =>
    api.post("/ml/safety/", destination ? { destination } : { latitude, longitude }),

  // Pass a destination id (uses its city/country), OR city/country directly.
  budget: ({ destination, city, country, days = 3, travelers = 1, budget_level = "mid" }) =>
    api.post("/ml/budget/", { destination, city, country, days, travelers, budget_level }),

  // Pass a destination id (its coords become the route endpoint), OR raw end_latitude/end_longitude.
  bestRoute: ({ start_latitude, start_longitude, destination, end_latitude, end_longitude }) =>
    api.post("/ml/best-route/", { start_latitude, start_longitude, destination, end_latitude, end_longitude }),
};

export default api;