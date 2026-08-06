import { motion } from "framer-motion"

const DestinationCardSkeleton = () => {
  return (
    <div className="card-base overflow-hidden rounded-2xl border animate-pulse">
      <div className="h-48 bg-gray-200 rounded-t-2xl" />
      <div className="p-4 space-y-3">
        <div className="h-5 bg-gray-200 rounded w-3/4" />
        <div className="h-4 bg-gray-200 rounded w-1/2" />
        <div className="h-4 bg-gray-200 rounded w-full" />
        <div className="h-4 bg-gray-200 rounded w-2/3" />
        <div className="h-10 bg-gray-200 rounded-xl w-full mt-3" />
      </div>
    </div>
  )
}

export default DestinationCardSkeleton
