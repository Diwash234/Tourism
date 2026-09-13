const Loader = ({ fullScreen = false, size = "md", text = "Loading..." }) => {
  const sizes = { sm: "h-5 w-5", md: "h-10 w-10", lg: "h-16 w-16" }
  const spinner = (
    <div className="flex flex-col items-center gap-3">
      <div
        className={`${sizes[size]} border-4 border-gray-200 border-t-primary-500 rounded-full animate-spin`}
      />
      {text && <p className="text-sm text-gray-500">{text}</p>}
    </div>
  )
  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white/80 backdrop-blur-sm z-[9999]">
        {spinner}
      </div>
    )
  }
  return <div className="flex items-center justify-center py-10">{spinner}</div>
}

export default Loader
