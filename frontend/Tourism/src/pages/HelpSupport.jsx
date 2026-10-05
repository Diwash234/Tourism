import { useState } from 'react'
import { Link } from 'react-router-dom'
import { FiChevronDown, FiChevronUp, FiMessageCircle, FiMail, FiFileText, FiAlertCircle } from 'react-icons/fi'
import axiosClient from '../api/axiosClient'

const CATEGORY_SUBJECTS = {
  general: 'General enquiry',
  booking: 'Booking issue',
  payment: 'Payment issue',
  technical: 'Technical issue',
  feedback: 'Feedback',
}

const HelpSupport = () => {
  const [openFaq, setOpenFaq] = useState(null)
  const [contactForm, setContactForm] = useState({ name: '', email: '', category: 'general', message: '' })
  const [submitted, setSubmitted] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState('')

  const faqs = [
    { q: 'How do I book a hotel?', a: 'Navigate to the Hotels page, select your preferred hotel, choose your dates, and click "Book Now". You will receive a confirmation email once your booking is confirmed.' },
    { q: 'How do I cancel a booking?', a: 'Go to My Bookings, find the booking you want to cancel, and click "Cancel". Cancellation policies vary by hotel.' },
    { q: 'How do I become a verified guide?', a: 'Apply through the Guide Application page. Submit your credentials, experience, and references. Our team will review and verify your application.' },
    { q: 'How do I report incorrect information?', a: 'Use the Feedback page to report any incorrect information. Our team will review and correct it.' },
    { q: 'How do I share my trip with others?', a: 'Open your itinerary, click "Share", and copy the link. Anyone with the link can view your trip without an account.' },
    { q: 'How do I enable offline mode?', a: 'Install the PWA (Progressive Web App) and enable offline mode in settings. Your itineraries and saved destinations will be available offline.' },
  ]

  // This used to fake a send: it flipped `submitted` on a 3s timer and threw
  // the message away, so "Message Sent!" was a lie. It now posts to the real
  // support endpoint (POST /feedback/) and only reports success on a 2xx.
  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setSending(true)
    try {
      await axiosClient.post('/feedback/', {
        name: contactForm.name.trim(),
        email: contactForm.email.trim(),
        category: 'general',
        subject: CATEGORY_SUBJECTS[contactForm.category] || 'Support request',
        message: `[${contactForm.category}] ${contactForm.message.trim()}`,
      })
      setSubmitted(true)
      setContactForm({ name: '', email: '', category: 'general', message: '' })
    } catch (err) {
      setError(
        err?.response?.data?.detail ||
          (err?.response
            ? 'We could not send your message. Please try again.'
            : 'Network problem — your message was not sent. Please try again.')
      )
    } finally {
      setSending(false)
    }
  }

  return (
    <div className="max-w-4xl mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Help & Support</h1>

      {/* FAQ */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Frequently Asked Questions</h2>
        <div className="space-y-2">
          {faqs.map((faq, idx) => (
            <div key={idx} className="border border-gray-200 dark:border-gray-700 rounded-lg">
              <button
                onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                className="w-full flex items-center justify-between p-4 text-left hover:bg-gray-50 dark:hover:bg-gray-800 rounded-lg"
              >
                <span className="font-medium">{faq.q}</span>
                {openFaq === idx ? <FiChevronUp className="w-5 h-5" /> : <FiChevronDown className="w-5 h-5" />}
              </button>
              {openFaq === idx && (
                <div className="px-4 pb-4 text-gray-600 dark:text-gray-400">
                  {faq.a}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Contact Form */}
      <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 mb-8">
        <h2 className="text-lg font-semibold mb-4">Contact Us</h2>
        {submitted ? (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <FiMessageCircle className="w-8 h-8 text-emerald-600" />
            </div>
            <h3 className="text-lg font-semibold text-emerald-600">Message Sent!</h3>
            <p className="text-gray-600 dark:text-gray-400 mt-2">We will get back to you within 24 hours.</p>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Name</label>
                <input
                  type="text"
                  value={contactForm.name}
                  onChange={(e) => setContactForm({ ...contactForm, name: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input
                  type="email"
                  value={contactForm.email}
                  onChange={(e) => setContactForm({ ...contactForm, email: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                  required
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Category</label>
              <select
                value={contactForm.category}
                onChange={(e) => setContactForm({ ...contactForm, category: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
              >
                <option value="general">General Inquiry</option>
                <option value="booking">Booking Issue</option>
                <option value="payment">Payment Issue</option>
                <option value="technical">Technical Issue</option>
                <option value="feedback">Feedback</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Message</label>
              <textarea
                value={contactForm.message}
                onChange={(e) => setContactForm({ ...contactForm, message: e.target.value })}
                rows={4}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
                required
              />
            </div>
            {error && (
              <div role="alert" className="flex items-start gap-2 rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">
                <FiAlertCircle className="mt-0.5 shrink-0" />
                <span>{error}</span>
              </div>
            )}
            <button
              type="submit"
              disabled={sending}
              className="px-6 py-2 bg-emerald-600 text-white rounded-lg font-medium hover:bg-emerald-700 disabled:opacity-50"
            >
              {sending ? 'Sending…' : 'Send Message'}
            </button>
          </form>
        )}
      </div>

      {/* Resources — these were plain divs advertising pages that do not exist
          ("Browse help articles", "Watch how-to guides"). They are now real
          links to surfaces that actually exist. */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <a
          href="mailto:support@nepalyatra.com"
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 text-center hover:border-emerald-400 transition-colors"
        >
          <FiMail className="w-8 h-8 mx-auto mb-3 text-emerald-600" />
          <h3 className="font-semibold mb-2">Email Support</h3>
          <p className="text-sm text-gray-500 break-all">support@nepalyatra.com</p>
        </a>
        <Link
          to="/how-it-works"
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 text-center hover:border-emerald-400 transition-colors"
        >
          <FiFileText className="w-8 h-8 mx-auto mb-3 text-emerald-600" />
          <h3 className="font-semibold mb-2">Knowledge Base</h3>
          <p className="text-sm text-gray-500">Browse help articles</p>
        </Link>
        <Link
          to="/emergency"
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 text-center hover:border-emerald-400 transition-colors"
        >
          <FiMessageCircle className="w-8 h-8 mx-auto mb-3 text-emerald-600" />
          <h3 className="font-semibold mb-2">Emergency Desk</h3>
          <p className="text-sm text-gray-500">Nearest police, hospital &amp; ambulance</p>
        </Link>
      </div>
    </div>
  )
}

export default HelpSupport
