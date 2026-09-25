const Loader = ({ fullScreen = false, size = "md", text = "Loading" }) => {
  const height = size === "sm" ? "h-5" : size === "lg" ? "h-16" : "h-10"
  const width = size === "sm" ? "w-5" : size === "lg" ? "w-16" : "w-10"
  return (
    <div className={`${fullScreen ? "min-h-[45vh] items-center justify-center" : "py-10 items-center justify-center"} flex`} role="status" aria-live="polite">
      <div className="flex flex-col items-center gap-3"><span className={`ny-skeleton rounded-full ${height} ${width}`} aria-hidden="true" />{text && <span className="text-sm text-[var(--ny-text-secondary)]">{text}…</span>}</div>
    </div>
  )
}

export default Loader
