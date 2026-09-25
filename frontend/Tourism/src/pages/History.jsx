import { useEffect, useState } from "react"
import PageHeader from "../components/common/PageHeader"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import { motion } from "framer-motion"
import { FiClock } from "react-icons/fi"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import ErrorState from "../components/ui/ErrorState"
import TravelTimeline from "../components/cards/TravelTimeline"
import { formatDate } from "../utils/helpers"

const History = () => {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  useEffect(() => {
    userApi
      .getHistory()
      .then(({ data }) => setHistory(data.results || data.items || data || []))
      .catch((requestError) => setError(requestError.response?.data?.detail || "We could not load your visit history right now."))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader />
  if (error) return <div className="ny-page container-app space-y-6 py-6 sm:py-8"><PageHeader title="Visit History" subtitle="Places you have opened or recorded in your Nepal Yatra workspace." icon={FiClock} /><ErrorState message={error} onRetry={() => window.location.reload()} /></div>

  // Reusing the same TravelTimeline component as Notifications.jsx for a
  // consistent "history of things that happened" visual language across
  // the app, rather than a one-off list layout just for this page.
  const timelineItems = history.map((item) => ({
    id: item.id,
    type: "itinerary",
    title: item.destination_detail?.name || "Unknown destination",
    description: item.destination_detail?.city,
    time: formatDate(item.viewed_at),
  }))

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className="ny-page space-y-6"
    >
      <CMSPageIntro pageKey="history" />
      <PageHeader title="Visit History" subtitle="Places you have opened or recorded in your Nepal Yatra workspace." icon={FiClock} />

      {history.length ? (
        <TravelTimeline items={timelineItems} />
      ) : (
        <EmptyState
          title="No history yet"
          subtitle="Your visited destinations will show up here."
        />
      )}
    </motion.div>
  )
}

export default History