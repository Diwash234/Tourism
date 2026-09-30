import { useState } from 'react'
import { FiUser, FiBell, FiLock, FiGlobe, FiTrash2, FiSave } from 'react-icons/fi'
import useAuth from '../hooks/useAuth'

const Settings = () => {
  const { user } = useAuth()
  const [activeTab, setActiveTab] = useState('account')
  const [saved, setSaved] = useState(false)

  const [account, setAccount] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    email: user?.email || '',
    phone_number: user?.phone_number || '',
  })

  const [notifications, setNotifications] = useState({
    email: true,
    sms: false,
    push: true,
    marketing: false,
    weekly_digest: false,
  })

  const [privacy, setPrivacy] = useState({
    profile_visible: true,
    location_sharing: true,
    show_activity: true,
  })

  const handleSave = () => {
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const tabs = [
    { id: 'account', label: 'Account', icon: <FiUser className="w-4 h-4" /> },
    { id: 'notifications', label: 'Notifications', icon: <FiBell className="w-4 h-4" /> },
    { id: 'privacy', label: 'Privacy', icon: <FiLock className="w-4 h-4" /> },
    { id: 'language', label: 'Language', icon: <FiGlobe className="w-4 h-4" /> },
  ]

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* Tabs */}
      <div className="flex gap-2 mb-6 border-b border-gray-200 dark:border-gray-700 pb-4">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-emerald-600 text-white'
                : 'text-gray-600 hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
            }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* Account Tab */}
      {activeTab === 'account' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold mb-4">Personal Information</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">First Name</label>
                <input
                  type="text"
                  value={account.first_name}
                  onChange={(e) => setAccount({ ...account, first_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Last Name</label>
                <input
                  type="text"
                  value={account.last_name}
                  onChange={(e) => setAccount({ ...account, last_name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input
                  type="email"
                  value={account.email}
                  onChange={(e) => setAccount({ ...account, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
                <input
                  type="tel"
                  value={account.phone_number}
                  onChange={(e) => setAccount({ ...account, phone_number: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
            <h2 className="text-lg font-semibold mb-4">Change Password</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Current Password</label>
                <input
                  type="password"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">New Password</label>
                <input
                  type="password"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Notifications Tab */}
      {activeTab === 'notifications' && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">Notification Preferences</h2>
          <div className="space-y-4">
            {[
              { key: 'email', label: 'Email Notifications', desc: 'Receive notifications via email' },
              { key: 'sms', label: 'SMS Notifications', desc: 'Receive notifications via SMS' },
              { key: 'push', label: 'Push Notifications', desc: 'Receive push notifications' },
              { key: 'marketing', label: 'Marketing Emails', desc: 'Receive promotional content' },
              { key: 'weekly_digest', label: 'Weekly Digest', desc: 'Weekly summary of destinations' },
            ].map(item => (
              <div key={item.key} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <p className="font-medium">{item.label}</p>
                  <p className="text-sm text-gray-500">{item.desc}</p>
                </div>
                <button
                  onClick={() => setNotifications({ ...notifications, [item.key]: !notifications[item.key] })}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    notifications[item.key] ? 'bg-emerald-600' : 'bg-gray-300'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    notifications[item.key] ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Privacy Tab */}
      {activeTab === 'privacy' && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">Privacy Settings</h2>
          <div className="space-y-4">
            {[
              { key: 'profile_visible', label: 'Public Profile', desc: 'Allow others to see your profile' },
              { key: 'location_sharing', label: 'Location Sharing', desc: 'Share your location with trusted contacts' },
              { key: 'show_activity', label: 'Show Activity', desc: 'Display your recent activity' },
            ].map(item => (
              <div key={item.key} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div>
                  <p className="font-medium">{item.label}</p>
                  <p className="text-sm text-gray-500">{item.desc}</p>
                </div>
                <button
                  onClick={() => setPrivacy({ ...privacy, [item.key]: !privacy[item.key] })}
                  className={`w-12 h-6 rounded-full transition-colors ${
                    privacy[item.key] ? 'bg-emerald-600' : 'bg-gray-300'
                  }`}
                >
                  <div className={`w-5 h-5 bg-white rounded-full shadow transition-transform ${
                    privacy[item.key] ? 'translate-x-6' : 'translate-x-0.5'
                  }`} />
                </button>
              </div>
            ))}
          </div>

          <div className="mt-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
            <h3 className="font-semibold text-red-800 dark:text-red-200 mb-2">Danger Zone</h3>
            <p className="text-sm text-red-600 dark:text-red-300 mb-4">
              Once you delete your account, there is no going back.
            </p>
            <button className="px-4 py-2 bg-red-600 text-white rounded-lg text-sm font-medium hover:bg-red-700 flex items-center gap-2">
              <FiTrash2 className="w-4 h-4" />
              Delete Account
            </button>
          </div>
        </div>
      )}

      {/* Language Tab */}
      {activeTab === 'language' && (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-lg font-semibold mb-4">Language Preference</h2>
          <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent">
            <option value="en">English</option>
            <option value="ne">नेपाली (Nepali)</option>
            <option value="hi">हिन्दी (Hindi)</option>
            <option value="zh">中文 (Chinese)</option>
            <option value="fr">Français (French)</option>
            <option value="de">Deutsch (German)</option>
            <option value="es">Español (Spanish)</option>
            <option value="ja">日本語 (Japanese)</option>
          </select>
        </div>
      )}

      {/* Save Button */}
      <div className="mt-6 flex items-center gap-4">
        <button
          onClick={handleSave}
          className="px-6 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 flex items-center gap-2"
        >
          <FiSave className="w-4 h-4" />
          Save Changes
        </button>
        {saved && (
          <span className="text-emerald-600 text-sm font-medium">Settings saved successfully!</span>
        )}
      </div>
    </div>
  )
}

export default Settings
