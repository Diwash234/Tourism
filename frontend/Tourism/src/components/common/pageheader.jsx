const THEMES = {
  coral: "from-primary-500 via-primary-600 to-ink",
  teal: "from-secondary-500 via-secondary-600 to-ink",
  blue: "from-blue-500 via-blue-600 to-ink",
  cyan: "from-cyan-500 via-cyan-600 to-ink",
  purple: "from-purple-500 via-purple-600 to-ink",
  indigo: "from-indigo-500 via-indigo-600 to-ink",
  amber: "from-marigold-500 via-marigold-600 to-ink",
  emerald: "from-emerald-500 via-emerald-600 to-ink",
  rose: "from-rose-500 via-rose-600 to-ink",
  red: "from-red-500 via-red-600 to-ink",
}

/**
 * Colored gradient banner used to give each page/dashboard its own visual identity.
 * theme: one of coral | teal | blue | cyan | purple | indigo | amber | emerald | rose | red
 * Every theme ends in the shared brand "ink" tone and carries the lungta
 * (prayer flag) strip + mountain-ridge silhouette signature for consistency.
 */
const PageHeader = ({ title, subtitle, icon: Icon, theme = "coral", actions }) => (
  <div className="relative overflow-hidden rounded-xl2 mb-8 shadow-card">
    <div className={`bg-gradient-to-br ${THEMES[theme] || THEMES.coral} text-white p-6 pb-8 relative`}>
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