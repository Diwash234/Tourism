import { useEffect, useState } from "react"
import userApi from "../api/userApi"
import Loader from "../components/common/Loader"
import EmptyState from "../components/common/EmptyState"
import { formatDate } from "../utils/helpers"
import { FiClock, FiMapPin } from "react-icons/fi"

const History = () => {
  const [history, setHistory] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    userApi
      .getHistory()
      .then(({ data }) => setHistory(data.items || data || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <Loader />

  return (
    <div>
      <h1 className="text-2xl font-bold mb-6">Visit History</h1>
      {history.length ? (
        <div className="space-y-4">
          {history.map((item) => (
            <div key={item.id} className="card-base p-4 flex items-center gap-4">
              <div className="p-3 rounded-full bg-primary-50 text-primary-500">
                <FiMapPin />
              </div>
              <div className="flex-1">
                <p className="font-semibold">{item.destinationName}</p>
                <p className="text-xs text-gray-400 flex items-center gap-1 mt-1">
                  <FiClock size={12} /> {formatDate(item.visitedAt)}
                </p>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <EmptyState title="No history yet" subtitle="Your visited destinations will show up here." />
      )}
    </div>
  )
}

export default History