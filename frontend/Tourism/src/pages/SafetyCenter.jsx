import { useState, useEffect } from 'react'
import { FiAlertTriangle, FiPhone, FiMapPin, FiShield, FiUsers, FiClock } from 'react-icons/fi'
import useAuth from '../hooks/useAuth'

const SafetyCenter = () => {
  const { user } = useAuth()
  const [emergencyContacts, setEmergencyContacts] = useState([])
  const [sosModal, setSosModal] = useState(false)
  const [sosLoading, setSosLoading] = useState(false)
  const [sosSuccess, setSosSuccess] = useState(false)

  useEffect(() => {
    fetchEmergencyContacts()
  }, [])

  const fetchEmergencyContacts = async () => {
    try {
      const response = await fetch('/api/v1/emergency/contacts/nearest/?latitude=27.7172&longitude=85.3240&radius_km=50')
      if (response.ok) {
        const data = await response.json()
        setEmergencyContacts(data)
      }
    } catch (err) {
      console.error('Failed to fetch emergency contacts:', err)
    }
  }

  const triggerSOS = async () => {
    setSosLoading(true)
    try {
      const response = await fetch('/api/v1/sos/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${localStorage.getItem('access')}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          latitude: 27.7172,
          longitude: 85.3240,
          message: 'Emergency SOS triggered'
        })
      })
      if (response.ok) {
        setSosSuccess(true)
        setTimeout(() => {
          setSosSuccess(false)
          setSosModal(false)
        }, 3000)
      }
    } catch (err) {
      console.error('Failed to trigger SOS:', err)
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
            onClick={() => setSosModal(true)}
            className="w-24 h-24 rounded-full bg-red-600 hover:bg-red-700 text-white font-bold text-sm flex items-center justify-center shadow-lg hover:shadow-xl transition-all active:scale-95"
          >
            SOS
          </button>
        </div>
      </div>

      {/* Emergency Contacts */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Emergency Contacts</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {emergencyContacts.length === 0 ? (
            <div className="col-span-2 text-center py-8 text-gray-500">
              <FiPhone className="w-8 h-8 mx-auto mb-2 opacity-50" />
              <p>No emergency contacts found nearby</p>
            </div>
          ) : (
            emergencyContacts.map((contact, idx) => (
              <div key={idx} className="flex items-center gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="w-10 h-10 rounded-full bg-emerald-100 dark:bg-emerald-900 flex items-center justify-center text-emerald-600">
                  {getContactIcon(contact.contact_type)}
                </div>
                <div className="flex-1">
                  <p className="font-medium">{contact.name}</p>
                  <p className="text-sm text-gray-500">{contact.contact_type}</p>
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
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-4">
                  <h3 className="text-lg font-semibold text-red-600">Confirm SOS Alert</h3>
                  <button onClick={() => setSosModal(false)} className="text-gray-400 hover:text-gray-600">
                    <FiX className="w-5 h-5" />
                  </button>
                </div>
                <p className="text-gray-600 dark:text-gray-400 mb-6">
                  This will immediately notify all your trusted contacts with your current location. Only use in genuine emergencies.
                </p>
                <div className="flex gap-3">
                  <button
                    onClick={() => setSosModal(false)}
                    className="flex-1 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                  <button
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
