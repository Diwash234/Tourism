import { Component } from "react"
import { FiAlertTriangle, FiRefreshCw } from "react-icons/fi"

/**
 * Error boundary that catches rendering errors and displays
 * a user-friendly fallback instead of crashing the whole app.
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, errorInfo) {
    console.error("ErrorBoundary caught:", error, errorInfo)
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="flex min-h-[320px] flex-col items-center justify-center gap-4 p-8 text-center">
          <div className="flex h-16 w-16 items-center justify-center rounded-2xl bg-red-50 text-red-500">
            <FiAlertTriangle size={32} />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900 dark:text-white">Something went wrong</h2>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              An unexpected error occurred. Please try refreshing the page.
            </p>
          </div>
          <button
            type="button"
            onClick={this.handleReset}
            className="inline-flex items-center gap-2 rounded-lg bg-[var(--ny-green)] px-4 py-2 text-sm font-semibold text-white hover:bg-[var(--ny-emerald)] transition-colors"
          >
            <FiRefreshCw size={16} />
            Try Again
          </button>
        </div>
      )
    }

    return this.props.children
  }
}

export default ErrorBoundary
