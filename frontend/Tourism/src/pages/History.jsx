import { useEffect, useState } from "react"
import { motion } from "framer-motion"
import { FiClock } from "react-icons/fi"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import TravelTimeline from "../components/cards/TravelTimeline"
import { formatDate } from "../utils/helpers"

const History = () => {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    userApi
      .getHistory()
      .then(({ data }) => setHistory(data.results || data.items || data || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader />

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
    <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="fade-in">
      <h1 className="section-title flex items-center gap-2">
        <FiClock className="text-himalaya-500" />
        Visit History
      </h1>
      {history.length ? (
        <TravelTimeline items={timelineItems} />
      ) : (
        <EmptyState title="No history yet" subtitle="Your visited destinations will show up here." />
      )}
    </motion.div>
  )
}

export default History