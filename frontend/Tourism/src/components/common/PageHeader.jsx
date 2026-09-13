const THEMES = {
  // Nepal-themed palette: deep mountain green, terracotta, Himalayan gold
  forest:  "from-[#1f6b4d] via-[#2a8562] to-[#143b2c]",
  mountain:"from-[#14503a] via-[#1f6b4d] to-[#0a281d]",
  terracotta: "from-[#c2603a] via-[#a34a29] to-[#6d2f18]",
  gold:    "from-[#b8862f] via-[#a3721f] to-[#6b4910]",
  cream:   "from-[#faf8f4] via-[#efe8d9] to-[#e5dcc5]",
  heritage:"from-[#7a1f1f] via-[#5a1515] to-[#2d0808]",
  lake:    "from-[#2f6f7f] via-[#245864] to-[#12323a]",
  // Legacy aliases (deprecated — kept so existing pages don't break)
  coral:   "from-[#c2603a] via-[#a34a29] to-[#6d2f18]",
  teal:    "from-[#1f6b4d] via-[#2a8562] to-[#143b2c]",
  amber:   "from-[#b8862f] via-[#a3721f] to-[#6b4910]",
  emerald: "from-[#1f6b4d] via-[#2a8562] to-[#143b2c]",
  rose:    "from-[#c2603a] via-[#a34a29] to-[#6d2f18]",
  red:     "from-[#7a1f1f] via-[#5a1515] to-[#2d0808]",
  blue:    "from-[#1f6b4d] via-[#2a8562] to-[#143b2c]",
  cyan:    "from-[#2f6f7f] via-[#245864] to-[#12323a]",
  purple:  "from-[#1f6b4d] via-[#2a8562] to-[#143b2c]",
  indigo:  "from-[#1f6b4d] via-[#2a8562] to-[#143b2c]",
}

/**
 * Colored gradient banner used to give each page/dashboard its own visual identity.
 * theme: forest | mountain | terracotta | gold | cream | heritage | lake
 *        (legacy: coral/teal/amber/emerald/rose/red map to the Nepal palette)
 * Every theme carries the lungta (prayer flag) strip + mountain-ridge silhouette.
 */
const PageHeader = ({ title, subtitle, icon: Icon, theme = "forest", actions }) => (
  <div className="relative overflow-hidden rounded-xl2 mb-8 shadow-card">
    <div className={`bg-gradient-to-br ${THEMES[theme] || THEMES.forest} text-white p-6 pb-8 relative`}>
      {/* Mountain-ridge silhouette, evokes the Himalayan skyline on every dashboard */}
      <svg
        className="absolute bottom-0 left-0 w-full h-16 opacity-20"
        viewBox="0 0 1200 160"
        preserveAspectRatio="none"
        aria-hidden="true"
      >
        <path
          d="M0,160 L0,90 L120,40 L220,100 L340,20 L460,90 L600,10 L740,95 L860,45 L980,110 L1100,55 L1200,90 L1200,160 Z"
          fill="white"
        />
      </svg>

      <div className="relative flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-display font-semibold flex items-center gap-2">
            {Icon && <Icon />} {title}
          </h1>
          {subtitle && <p className="text-white/85 text-sm mt-1 max-w-xl">{subtitle}</p>}
        </div>
        {actions && <div className="relative flex items-center gap-2">{actions}</div>}
      </div>
    </div>
    <div className="lungta-strip" />
  </div>
)

export default PageHeader
