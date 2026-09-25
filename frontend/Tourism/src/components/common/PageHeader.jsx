/**
 * One traveller-facing page header. The old component exposed a different
 * gradient for almost every page, which made the product feel like several
 * applications. `theme` remains accepted for CMS/page compatibility, but all
 * public pages now share the same quiet Nepal-green treatment.
 */
const PageHeader = ({ title, subtitle, icon: Icon, actions, theme: _theme, eyebrow = "Nepal Yatra", className = "" }) => (
  <header className={`ny-page-header relative mb-6 overflow-hidden rounded-[var(--ny-radius-lg)] bg-[var(--ny-green-dark)] text-white shadow-[var(--ny-shadow)] sm:mb-8 ${className}`}>
    <div className="pointer-events-none absolute inset-0 opacity-70" aria-hidden="true" style={{ background: "radial-gradient(circle at 85% 15%, rgba(99,230,190,0.18), transparent 32%), linear-gradient(120deg, transparent 0 55%, rgba(245,181,27,0.08) 100%)" }} />
    <div className="relative flex flex-col gap-5 p-5 sm:p-7 lg:flex-row lg:items-center lg:justify-between">
      <div className="min-w-0 flex-1">
        <div className="flex items-start gap-3">
          {Icon && <span className="mt-1 grid h-10 w-10 shrink-0 place-items-center rounded-[var(--ny-radius-md)] bg-white/10 text-[#BDEBD9]"><Icon size={20} aria-hidden="true" /></span>}
          <div className="min-w-0">
            {eyebrow && <p className="mb-2 text-xs font-bold uppercase tracking-[0.14em] text-[#BDEBD9]">{eyebrow}</p>}
            <h1 className="!m-0 !text-white">{title}</h1>
            {subtitle && <p className="mt-2 max-w-3xl text-[0.95rem] leading-6 text-[#C7D9D2]">{subtitle}</p>}
          </div>
        </div>
      </div>
      {actions && <div className="flex w-full shrink-0 flex-wrap items-center gap-3 lg:w-auto lg:justify-end">{actions}</div>}
    </div>
    <div className="relative h-1 bg-[var(--ny-gold)]" aria-hidden="true" />
  </header>
)

export default PageHeader
