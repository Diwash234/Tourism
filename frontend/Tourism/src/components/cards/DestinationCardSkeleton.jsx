const DestinationCardSkeleton = () => (
  <div className="ny-card overflow-hidden" aria-hidden="true">
    <div className="ny-skeleton h-48 rounded-none" />
    <div className="space-y-3 p-5">
      <div className="ny-skeleton h-5 w-3/4" />
      <div className="ny-skeleton h-4 w-1/2" />
      <div className="ny-skeleton h-4 w-2/3" />
      <div className="ny-skeleton h-11 w-full" />
    </div>
  </div>
)

export default DestinationCardSkeleton
