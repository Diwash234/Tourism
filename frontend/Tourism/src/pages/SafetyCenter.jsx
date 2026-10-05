import { useCallback, useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { FiAlertTriangle, FiPhone, FiMapPin, FiShield, FiUsers, FiClock, FiX, FiAlertCircle, FiNavigation } from 'react-icons/fi'
import useAuth from '../hooks/useAuth'
import emergencyService from '../api/emergencyService'
import safetyApi from '../api/safetyApi'
import useGeolocation from '../hooks/useGeolocation'

/**
 * Safety centre.
 *
 * Previously inert in two ways:
 *  - it called /api/v1/emergency/contacts/nearest/ and /api/v1/sos/, neither
 *    of which exists (the real routes are /emergency-contacts/nearest/ and
 *    /safety/sos/), so the contact list never loaded and SOS never sent;
 *  - both calls sent hardcoded Kathmandu coordinates (27.7172, 85.3240), so
 *    even after fixing the URLs it would have reported the wrong services.
 *
 * It now uses the real API clients, asks the browser for the traveller's
 * actual position, and surfaces failures instead of silently doing nothing.
 */

// Falls back to Kathmandu only when the browser refuses to share a position,
// so "nearby" is never silently the wrong city.
const FALLBACK = { latitude: 27.7172, longitude: 85.3240 }

const SafetyCenter = () => {
  const { isAuthenticated } = useAuth()
  const navigate = useNavigate()
  const { latitude, longitude, loading: locating, error: locationError, source } = useGeolocation()

  const [emergencyContacts, setEmergencyContacts] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState('')
  const [sosModal, setSosModal] = useState(false)
  const [sosLoading, setSosLoading] = useState(false)
  const [sosSuccess, setSosSuccess] = useState(false)
  const [sosError, setSosError] = useState('')

  const hasFix = latitude != null && longitude != null
  const coords = hasFix ? { latitude, longitude } : FALLBACK

  const fetchEmergencyContacts = useCallback(() => {
    setLoading(true)
    setLoadError('')
    emergencyService.nearby(coords.latitude, coords.longitude)
      .then(({ data }) => {
        const list = Array.isArray(data) ? data : data?.results || []
        setEmergencyContacts(list)
        if (list.length === 0) setLoadError('')
      })
      .catch(() => {
        setEmergencyContacts([])
        setLoadError('Nearby emergency services could not be loaded right now.')
      })
      .finally(() => setLoading(false))
  }, [coords.latitude, coords.longitude])

  useEffect(() => {
    const t = setTimeout(fetchEmergencyContacts, 0)
    return () => clearTimeout(t)
  }, [fetchEmergencyContacts])

  const openSos = () => {
    if (!isAuthenticated) {
      navigate('/login', { state: { from: '/safety-center' } })
      return
    }
    setSosError('')
    setSosSuccess(false)
    setSosModal(true)
  }

  const triggerSOS = async () => {
    setSosLoading(true)
    setSosError('')
    try {
      await safetyApi.triggerSos({
        latitude: coords.latitude,
        longitude: coords.longitude,
        message: 'Emergency SOS triggered',
      })
      setSosSuccess(true)
    } catch (error) {
      const detail =
        error?.response?.data?.detail ||
        'We could not send your SOS alert. Call the local emergency number directly.'
      setSosError(detail)
    } finally {
      setSosLoading(false)
    }
  }

  const getContactIcon = (type) => {
    const icons = {
      police: <FiShield className="w-5 h-5" />,
      hospital: <FiAlertTriangle className="w-5 h-5" />,
      ambulance: <FiAlertTriangle className="w-5 h-5" />,
      fire_station: <FiAlertTriangle className="w-5 h-5" />,
    }
    return icons[type] || <FiPhone className="w-5 h-5" />
  }

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Safety Center</h1>

      {/* SOS Button */}
      <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-xl p-6 mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-red-800 dark:text-red-200">Emergency SOS</h2>
            <p className="text-red-600 dark:text-red-300 text-sm mt-1">
              Tap the button to send an emergency alert to your trusted contacts
            </p>
          </div>
          <button
            type="button"
            onClick={openSos}
            className="w-24 h-24 rounded-full bg-red-600 hover:bg-red-700 text-white font-bold text-sm flex items-center justify-center shadow-lg hover:shadow-xl transition-all active:scale-95"
          >
            SOS
          </button>
        </div>
      </div>

      {/* Emergency Contacts */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-8">
        <div className="flex items-center justify-between gap-3 mb-4">
          <h2 className="text-lg font-semibold">Emergency Contacts</h2>
          <span className="inline-flex items-center gap-1 text-xs text-gray-500">
            <FiNavigation className={locating ? 'animate-pulse' : ''} />
            {locating ? 'Finding you…' : hasFix ? `Near your location${source === 'ip' ? ' (approx.)' : ''}` : 'Using Kathmandu (location unavailable)'}
          </span>
        </div>
        {(loadError || locationError) && (
          <div role="alert" className="mb-4 flex items-center gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
            <FiAlertCircle />
            <span>{loadError || locationError}</span>
            <button type="button" onClick={fetchEmergencyContacts} className="ml-auto font-semibold underline">Retry</button>
          </div>
        )}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {loading ? (
            <div className="col-span-2 text-center py-8 text-gray-500">Loading nearby services…</div>
          ) : emergencyContacts.length === 0 ? (
            <div className="col-span-2 text-center py-8 text-gray-500">
              <FiPhone className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No emergency contacts found nearby</p>
            </div>
          ) : (
            emergencyContacts.map((contact, idx) => (
              <div key={contact.id || idx} className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center text-emerald-600">
                  {getContactIcon(contact.contact_type)}
                </div>
                <div className="flex-1">
                  <p className="font-medium">{contact.name}</p>
                  <p className="text-sm text-gray-500">
                    {contact.contact_type}
                    {contact.distance_km != null && ` · ${Number(contact.distance_km).toFixed(1)} km`}
                  </p>
                </div>
                <a
                  href={`tel:${contact.phone_number}`}
                  className="px-4 py-2 bg-emerald-600 text-white rounded-lg text-sm font-medium hover:bg-emerald-700"
                >
                  Call
                </a>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Safety Tips */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Safety Tips</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[
            { icon: <FiMapPin className="w-5 h-5" />, title: 'Share Your Location', desc: 'Always share your live location with trusted contacts when traveling.' },
            { icon: <FiUsers className="w-5 h-5" />, title: 'Travel in Groups', desc: 'Avoid traveling alone, especially in remote areas.' },
            { icon: <FiClock className="w-5 h-5" />, title: 'Plan Ahead', desc: 'Inform someone about your itinerary and expected return time.' },
            { icon: <FiShield className="w-5 h-5" />, title: 'Stay Informed', desc: 'Check weather and road conditions before traveling.' },
          ].map((tip, idx) => (
            <div key={idx} className="flex gap-3 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
              <div className="text-emerald-600">{tip.icon}</div>
              <div>
                <p className="font-medium">{tip.title}</p>
                <p className="text-sm text-gray-500 mt-1">{tip.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* SOS Modal */}
      {sosModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-900 rounded-xl p-6 max-w-md w-full mx-4">
            {sosSuccess ? (
              <div className="text-center">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <FiShield className="w-8 h-8 text-emerald-600" />
                </div>
                <h3 className="text-lg font-semibold text-emerald-600">SOS Alert Sent!</h3>
                <p className="text-gray-600 dark:text-gray-400 mt-2">
                  Your trusted contacts have been notified of your location.
                </p>
                <button
                  type="button"
                  onClick={() => { setSosModal(false); setSosSuccess(false) }}
                  className="mt-6 px-5 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700"
                >
                  Close
                </button>
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-red-600">Confirm SOS Alert</h3>
                  <button type="button" onClick={() => setSosModal(false)} aria-label="Close" className="text-gray-400 hover:text-gray-600">
                    <FiX className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  This will immediately notify all your trusted contacts with your current location. Only use in genuine emergencies.
                </p>
                <p className="mb-4 text-xs text-gray-500">
                  Sending from {hasFix ? 'your current GPS position' : 'Kathmandu (your location was not shared)'}.
                </p>
                {sosError && (
                  <div role="alert" className="mb-4 flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                    <FiAlertCircle className="mt-0.5 shrink-0" />
                    <span>{sosError}</span>
                  </div>
                )}
                <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={() => setSosModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="button"
                    onClick={triggerSOS}
                    disabled={sosLoading}
                    className="flex-1 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50"
                  >
                    {sosLoading ? 'Sending...' : 'Send SOS'}
                  </button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default SafetyCenter
