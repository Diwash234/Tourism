const Loader = ({ fullScreen = false, size = "md" }) => {
  const sizes = { sm: "h-5 w-5", md: "h-10 w-10", lg: "h-16 w-16" }
  const spinner = (
    <div
      className={`${sizes[size]} border-4 border-gray-200 border-t-primary-500 rounded-full animate-spin`}
    />
  )
  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white/70 z-[9999]">
        {spinner}
      </div>
    )
  }
  return <div className="flex items-center justify-center py-10">{spinner}</div>
}

export default Loader