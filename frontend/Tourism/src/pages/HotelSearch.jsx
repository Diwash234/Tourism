import { useEffect, useRef, useState } from "react"
import { Link, useSearchParams } from "react-router-dom"
import { FiMapPin, FiSearch } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import EmptyState from "../components/common/EmptyState"
import SkeletonLoader from "../components/common/SkeletonLoader"
import HotelCard from "../components/cards/HotelCard"
import CMSPageIntro from "../components/cms/CMSPageIntro"
import hotelApi from "../api/hotelApi"
import useAuth from "../hooks/useAuth"
import { useI18n } from "../i18n"

export default function HotelSearch() {
  const { t } = useI18n()
  const [searchParams, setSearchParams] = useSearchParams()
  const urlQuery = (searchParams.get("q") || "").trim()
  const [query, setQuery] = useState(urlQuery)
  const [hotels, setHotels] = useState([])
  const [loading, setLoading] = useState(false)
  const [searched, setSearched] = useState(false)
  const [error, setError] = useState("")
  const { isAuthenticated } = useAuth()

  const lastUrlQuery = useRef("")
  const runSearch = async (text) => {
    if (!text) {
      setError(t("hotelsearch.enter_query"))
      return
    }
    setLoading(true)
    setSearched(true)
    setError("")
    setHotels([])
    try {
      const data = await hotelApi.search(text)
      setHotels(Array.isArray(data?.results) ? data.results : Array.isArray(data) ? data : [])
    } catch (requestError) {
      setError(requestError.response?.data?.detail || t("hotelsearch.load_error"))
    } finally {
      setLoading(false)
    }
  }

  const handleSearch = (event) => {
    event.preventDefault()
    const text = query.trim()
    if (text && text !== urlQuery) {
      lastUrlQuery.current = text // the URL change below must not search twice
      setSearchParams({ q: text }, { replace: true })
    }
    runSearch(text)
  }

  // /hotels/search?q=… (site search "See all", header links) searches on arrival.
  useEffect(() => {
    if (!urlQuery || urlQuery === lastUrlQuery.current) return
    lastUrlQuery.current = urlQuery
    const t = setTimeout(() => { setQuery(urlQuery); runSearch(urlQuery) }, 0)
    return () => clearTimeout(t)
    // runSearch is recreated each render; the URL query is the trigger.
  }, [urlQuery])

  return (
    <div className="ny-page container-app space-y-6 py-6 sm:py-8">
      <CMSPageIntro pageKey="hotel-search" />
      <PageHeader title={t("hotelsearch.title")} subtitle={t("hotelsearch.subtitle")} />

      <form onSubmit={handleSearch} className="ny-panel flex flex-col gap-3 p-4 sm:flex-row" role="search">
        <div className="relative min-w-0 flex-1">
          <FiSearch size={17} className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 text-[var(--ny-text-muted)]" aria-hidden="true" />
          <label htmlFor="hotel-search" className="sr-only">{t("hotelsearch.search_label")}</label>
          <input id="hotel-search" className="input-field pl-11" placeholder={t("hotelsearch.search_placeholder")} value={query} onChange={(event) => setQuery(event.target.value)} />
        </div>
        <button className="ny-btn ny-btn-primary" type="submit" disabled={loading}>{loading ? t("hotelsearch.searching") : t("hotelsearch.search_cta")}</button>
      </form>

      {error && <div role="alert" className="ny-panel border-[#E9B9B9] bg-[var(--ny-soft-red)] p-4 text-sm text-[var(--ny-danger)]">{error}</div>}
      {loading ? <SkeletonLoader count={6} /> : searched && hotels.length === 0 && !error ? (
        <EmptyState title={t("hotelsearch.no_match_title")} subtitle={t("hotelsearch.no_match_sub")} action={<Link to="/destinations" className="ny-btn ny-btn-primary">{t("hotelsearch.browse_destinations")}</Link>} />
      ) : hotels.length > 0 ? (
        <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {hotels.map((hotel) => {
            const bookingPath = `/hotels/${hotel.id}/book`
            return (
              <div key={hotel.id} className="flex h-full flex-col">
                <HotelCard hotel={hotel} />
                <Link to={isAuthenticated ? bookingPath : `/login?next=${encodeURIComponent(bookingPath)}`} className="ny-btn ny-btn-secondary mt-3 w-full">
                  {t("hotelsearch.request_booking")}
                </Link>
              </div>
            )
          })}
        </div>
      ) : (
        <EmptyState title={t("hotelsearch.empty_title")} subtitle={t("hotelsearch.empty_sub")} action={<Link to="/destinations" className="ny-btn ny-btn-secondary"><FiMapPin size={15} aria-hidden="true" />{t("hotelsearch.browse_destinations")}</Link>} />
      )}
    </div>
  )
}
