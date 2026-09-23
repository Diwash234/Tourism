import { Link, useLocation } from "react-router-dom"
import { FiChevronRight, FiHome } from "react-icons/fi"
import { useI18n } from "../../i18n"

export default function Breadcrumbs({ items = [] }) {
  const { t } = useI18n()
  const location = useLocation()

  // Generate breadcrumb list if not explicitly passed
  const pathnames = location.pathname.split("/").filter((x) => x)
  const breadcrumbs = items.length > 0 ? items : pathnames.map((value, index) => {
    const to = `/${pathnames.slice(0, index + 1).join("/")}`
    const label = value.charAt(0).toUpperCase() + value.slice(1).replace(/-/g, " ")
    return { label, to }
  })

  if (breadcrumbs.length === 0) return null

  // JSON-LD Breadcrumb Schema for SEO
  const schemaData = {
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": "https://nepaltourism.gov.np/",
      },
      ...breadcrumbs.map((b, i) => ({
        "@type": "ListItem",
        "position": i + 2,
        "name": b.label,
        "item": `https://nepaltourism.gov.np${b.to}`,
      })),
    ],
  }

  return (
    <>
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(schemaData) }}
      />
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-gray-500 py-2 mb-4 overflow-x-auto no-scrollbar">
        <Link to="/" className="hover:text-[#102A2E] flex items-center gap-1 font-medium">
          <FiHome size={12} /> Home
        </Link>
        {breadcrumbs.map((b, idx) => {
          const isLast = idx === breadcrumbs.length - 1
          return (
            <div key={idx} className="flex items-center gap-1.5 shrink-0">
              <FiChevronRight size={12} className="text-gray-300" />
              {isLast ? (
                <span className="font-bold text-[#102A2E] truncate max-w-[200px]" aria-current="page">
                  {b.label}
                </span>
              ) : (
                <Link to={b.to} className="hover:text-[#102A2E] font-medium truncate max-w-[150px]">
                  {b.label}
                </Link>
              )}
            </div>
          )
        })}
      </nav>
    </>
  )
}
