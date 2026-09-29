import { Link } from "react-router-dom"
import Breadcrumbs from "../common/Breadcrumbs"
import usePublicConfig from "../../hooks/usePublicConfig"
import CMSPageIntro from "../cms/CMSPageIntro"

export const LEGAL_UPDATED = "26 September 2026"

/** Contact line from the admin-configured branding; never a made-up address. */
export function LegalContact() {
  const { branding = {} } = usePublicConfig()
  const email = /@example\.(com|org)$/i.test(String(branding.contact_email || "")) ? "" : branding.contact_email
  return (
    <p>
      {email ? <>Email <a className="ny-legal-link" href={`mailto:${email}`}>{email}</a> or use the </> : "Use the "}
      <Link className="ny-legal-link" to="/contact">contact page</Link>. Please do not send passwords or card numbers.
    </p>
  )
}

/**
 * Shared layout for policy pages: one h1, a last-updated date, an in-page
 * table of contents and numbered sections with stable anchors.
 */
export default function LegalPage({ title, path, intro, sections, pageKey }) {
  return (
    <div className="container-app py-8">
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: title, to: path }]} />
      <article className="ny-reading ny-card mt-4 p-6 text-[var(--ny-text)] sm:p-8">
        <header className="border-b border-[var(--ny-border)] pb-5">
          <h1 className="text-3xl font-black tracking-tight">{title}</h1>
          <p className="mt-2 text-sm text-[var(--ny-text-secondary)]">Last updated {LEGAL_UPDATED}</p>
          {intro && <div className="mt-4 space-y-3 text-[0.95rem] leading-7 text-[var(--ny-text-secondary)]">{intro}</div>}
        </header>
        <nav aria-label="On this page" className="mt-5 rounded-[var(--ny-radius-md)] bg-[var(--ny-bg)] p-4">
          <p className="text-xs font-bold uppercase tracking-wide text-[var(--ny-text-secondary)]">On this page</p>
          <ol className="mt-2 grid gap-1 text-sm sm:grid-cols-2">
            {sections.map((s, i) => <li key={s.id}><a className="ny-legal-link" href={`#${s.id}`}>{i + 1}. {s.title}</a></li>)}
          </ol>
        </nav>
        <div className="mt-6 space-y-7 text-[0.95rem] leading-7 text-[var(--ny-text-secondary)]">
          {sections.map((s, i) => (
            <section key={s.id} id={s.id} aria-labelledby={`${s.id}-h`} className="scroll-mt-24 space-y-3">
              <h2 id={`${s.id}-h`} className="text-lg font-bold text-[var(--ny-text)]">{i + 1}. {s.title}</h2>
              {s.body}
            </section>
          ))}
        </div>
      </article>
      {/* Extra sections an editor adds in Admin -> CMS. The policy text above
          stays in code because it must match what the code actually does. */}
      {pageKey && <CMSPageIntro pageKey={pageKey} />}
    </div>
  )
}

/** Simple two-column table that stacks on narrow screens (no sideways scroll). */
export function LegalTable({ caption, head, rows }) {
  return (
    <table className="ny-legal-table w-full text-left text-sm">
      {caption && <caption className="mb-2 text-left font-semibold text-[var(--ny-text)]">{caption}</caption>}
      <thead><tr>{head.map((h) => <th key={h} scope="col">{h}</th>)}</tr></thead>
      <tbody>
        {rows.map((row) => (
          <tr key={row[0]}>{row.map((cell, i) => (i === 0 ? <th key={i} scope="row">{cell}</th> : <td key={i} data-label={head[i]}>{cell}</td>))}</tr>
        ))}
      </tbody>
    </table>
  )
}
