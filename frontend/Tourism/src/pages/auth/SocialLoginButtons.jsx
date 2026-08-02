import { FiGithub } from "react-icons/fi"
import { getGoogleAuthUrl, getGithubAuthUrl } from "../../utils/oauth"

// A simple original "G" mark instead of importing Google's actual logo
// asset (brand guidelines require using their exact provided SVG, which
// isn't bundled in this project) — clearly recognizable as Google via
// color + label without misrepresenting an official asset.
const GoogleMark = () => (
  <svg viewBox="0 0 24 24" width="18" height="18">
    <path fill="#4285F4" d="M23.5 12.3c0-.8-.1-1.6-.2-2.3H12v4.5h6.5c-.3 1.5-1.1 2.7-2.4 3.6v3h3.9c2.3-2.1 3.5-5.3 3.5-8.8z" />
    <path fill="#34A853" d="M12 24c3.2 0 5.9-1.1 7.9-2.9l-3.9-3c-1.1.7-2.4 1.1-4 1.1-3.1 0-5.7-2.1-6.6-4.9H1.4v3.1C3.4 21.3 7.4 24 12 24z" />
    <path fill="#FBBC05" d="M5.4 14.3c-.2-.7-.4-1.5-.4-2.3s.1-1.6.4-2.3V6.6H1.4C.5 8.3 0 10.1 0 12s.5 3.7 1.4 5.4l4-3.1z" />
    <path fill="#EA4335" d="M12 4.8c1.7 0 3.3.6 4.5 1.8l3.4-3.4C17.9 1.2 15.2 0 12 0 7.4 0 3.4 2.7 1.4 6.6l4 3.1c.9-2.8 3.5-4.9 6.6-4.9z" />
  </svg>
)

/**
 * SocialLoginButtons
 * Redirects the browser (not a popup) to the provider's consent screen —
 * see utils/oauth.js. OAuthCallback.jsx handles the return trip.
 */
const SocialLoginButtons = () => (
  <div className="space-y-3">
    <div className="flex items-center gap-3">
      <div className="flex-1 h-px bg-gray-200" />
      <span className="text-xs text-gray-400">or continue with</span>
      <div className="flex-1 h-px bg-gray-200" />
    </div>

    <div className="grid grid-cols-2 gap-3">
      <a
        href={getGoogleAuthUrl()}
        className="flex items-center justify-center gap-2 border border-gray-200 rounded-xl py-2.5 text-sm font-medium hover:bg-gray-50 transition-colors"
      >
        <GoogleMark /> Google
      </a>
      <a
        href={getGithubAuthUrl()}
        className="flex items-center justify-center gap-2 border border-gray-200 rounded-xl py-2.5 text-sm font-medium hover:bg-gray-50 transition-colors"
      >
        <FiGithub size={18} /> GitHub
      </a>
    </div>
  </div>
)

export default SocialLoginButtons