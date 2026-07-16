const ErrorMessage = ({ message }) => (
  <div className="bg-red-50 text-red-600 text-sm rounded-xl px-4 py-3 border border-red-100">
    {message || "Something went wrong. Please try again."}
  </div>
)

export default ErrorMessage