/**
 * Skeleton loading placeholder with multiple variants.
 */
export default function Skeleton({ variant = "text", width, height, className = "" }) {
  const variants = {
    text: "h-4 rounded",
    title: "h-6 rounded-lg",
    avatar: "rounded-full",
    card: "rounded-2xl",
    image: "rounded-xl",
    button: "h-10 rounded-lg",
  }

  const style = {
    width: width || (variant === "avatar" ? "40px" : variant === "card" ? "100%" : "100%"),
    height: height || (variant === "avatar" ? "40px" : variant === "card" ? "200px" : variant === "image" ? "200px" : variant === "title" ? "24px" : variant === "button" ? "40px" : "16px"),
  }

  return (
    <div
      className={`animate-pulse bg-gray-200 dark:bg-slate-700 ${variants[variant] || variants.text} ${className}`}
      style={style}
      aria-hidden="true"
    />
  )
}

export function SkeletonCard() {
  return (
    <div className="bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-2xl p-5 space-y-4">
      <div className="flex items-center gap-3">
        <Skeleton variant="avatar" width="40px" height="40px" />
        <div className="flex-1 space-y-2">
          <Skeleton variant="text" width="60%" />
          <Skeleton variant="text" width="40%" />
        </div>
      </div>
      <Skeleton variant="image" width="100%" height="180px" />
      <div className="space-y-2">
        <Skeleton variant="text" width="100%" />
        <Skeleton variant="text" width="80%" />
        <Skeleton variant="text" width="60%" />
      </div>
    </div>
  )
}

export function SkeletonList({ count = 5 }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="flex items-center gap-3 p-3 bg-white dark:bg-slate-800 border border-[var(--ny-border)] rounded-xl">
          <Skeleton variant="avatar" width="36px" height="36px" />
          <div className="flex-1 space-y-2">
            <Skeleton variant="text" width="50%" />
            <Skeleton variant="text" width="30%" />
          </div>
        </div>
      ))}
    </div>
  )
}
