export default function SkeletonLoader({ count = 3, type = "card" }) {
  if (type === "text") {
    return (
      <div className="space-y-2 animate-pulse">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="h-4 bg-emerald-100/70 rounded-lg w-full" />
        ))}
      </div>
    )
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 animate-pulse">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="bg-[#F7F8F5]/50 border border-[#E5E0D5] rounded-3xl overflow-hidden p-4 space-y-3">
          <div className="h-44 bg-purple-200/50 rounded-2xl w-full" />
          <div className="h-5 bg-purple-200/60 rounded-md w-3/4" />
          <div className="h-3 bg-emerald-100 rounded-md w-1/2" />
          <div className="h-8 bg-purple-200/40 rounded-xl w-full" />
        </div>
      ))}
    </div>
  )
}
