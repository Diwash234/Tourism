/**
 * Global React ErrorBoundary. Any rendering error in its subtree is
 * reported to the backend audit endpoint and shown as a friendly
 * "Something broke on this screen" card instead of a white page.
 */
import { Component } from "react"
import { FiAlertTriangle, FiRefreshCw } from "react-icons/fi"
import { reportError } from "../../utils/errorLogger"

export default class ErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    reportError(error, {
      component: this.props.name || "ErrorBoundary",
      extra: { componentStack: info?.componentStack || "" },
    })
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null })
    if (this.props.onReset) this.props.onReset()
    else window.location.reload()
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="ny-panel mx-auto my-10 max-w-xl p-8 text-center">
          <div className="w-14 h-14 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center mx-auto mb-4">
            <FiAlertTriangle size={28} />
          </div>
          <h2 className="text-xl font-bold text-stone-900 mb-2">
            Something went wrong on this screen
          </h2>
          <p className="text-sm text-stone-600 mb-5">
            The page could not be displayed. Your account and saved data were not changed. Try reloading this section.
          </p>
          <button
            onClick={this.handleReset}
            className="ny-btn ny-btn-primary inline-flex items-center gap-2"
          >
            <FiRefreshCw /> Reload this section
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
