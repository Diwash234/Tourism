const ErrorMessage = ({ message }) => (
  <div className="bg-nepalred-50 text-nepalred-600 text-sm rounded-xl px-4 py-3 border border-nepalred-100">
    {message || "Something went wrong. Please try again."}
  </div>
)

export default ErrorMessage