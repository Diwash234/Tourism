const CardSkeleton = () => (
  <div className="ny-card overflow-hidden" aria-hidden="true">
    <div className="ny-skeleton h-48 w-full rounded-none" />
    <div className="space-y-3 p-5">
      <div className="ny-skeleton h-5 w-3/4" />
      <div className="ny-skeleton h-4 w-1/2" />
      <div className="ny-skeleton h-10 w-full" />
    </div>
  </div>
)

const SkeletonLoader = ({ count = 3, type = "card" }) => {
  if (type === "text") {
    return (
      <div className="space-y-3" aria-label="Loading" role="status">
        {Array.from({ length: count }).map((_, i) => <div key={i} className="ny-skeleton h-4 w-full" />)}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-2 min-[1240px]:grid-cols-3" role="status" aria-label="Loading">
      {Array.from({ length: count }).map((_, i) => <CardSkeleton key={i} />)}
    </div>
  )
}

export default SkeletonLoader
