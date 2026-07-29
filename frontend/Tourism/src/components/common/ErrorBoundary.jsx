import { Component } from "react"

/**
 * Wrap the app (see main.jsx) so any render-time crash shows a visible
 * error instead of a blank white screen. This is what "View Details did
 * nothing" almost certainly was — some destinations have missing/odd
 * fields (null lat/lng, no slug, etc.) that crashed the render with no
 * feedback. Wrapping App here won't fix the root data issue by itself,
 * but it turns every future "blank page" into a readable error + stack,
 * which is what you need to actually diagnose the next one.
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error("App crashed:", error, info.componentStack)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="min-h-screen flex items-center justify-center p-8">
          <div className="card-base max-w-lg p-6 border border-nepalred-100">
            <h1 className="text-lg font-bold text-nepalred-500 mb-2">Something broke on this page</h1>
            <p className="text-sm text-gray-600 mb-3">
              {this.state.error?.message || "Unknown error"}
            </p>
            <p className="text-xs text-gray-400 mb-4">
              Open the browser console for the full stack trace.
            </p>
            <button className="btn-outline" onClick={() => window.location.assign("/dashboard")}>
              Back to Dashboard
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

export default ErrorBoundary