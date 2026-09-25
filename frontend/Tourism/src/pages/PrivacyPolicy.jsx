import { Link } from "react-router-dom"
import { FiShield } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { ResponsiveContainer } from "../components/common/ResponsiveSystem"
import CMSPageIntro from "../components/cms/CMSPageIntro"

export default function PrivacyPolicy() {
  return (
    <ResponsiveContainer className="py-8 space-y-6">
      <Breadcrumbs items={[
        { label: "Home", to: "/" },
        { label: "Privacy Policy", to: "/privacy" }
      ]} />

      <div className="ny-reading ny-card p-6 text-[var(--ny-text)] sm:p-8">
        <div>
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-bold uppercase">
            Data Protection & Privacy
          </span>
          <CMSPageIntro pageKey="privacy-policy" />
          <PageHeader title="Privacy Policy" subtitle="How Nepal Yatra handles information you choose to share." icon={FiShield} />
        </div>

        <div className="space-y-5 text-[0.95rem] leading-7 text-[var(--ny-text-secondary)] border-t border-[var(--ny-border)] pt-5">
          <section className="space-y-1">
            <h2 className="text-lg font-bold text-[var(--ny-text)]">1. Information We Collect</h2>
            <p>We collect information you explicitly provide when creating an account, searching destinations, filing error reports, or submitting travel preferences. Geolocation data is requested only with your explicit browser consent.</p>
          </section>

          <section className="space-y-1">
            <h2 className="text-lg font-bold text-[var(--ny-text)]">2. How Data is Used</h2>
            <p>Your preferences and interaction signals are used to generate personalized recommendations, calculate real-time travel routes, and deliver safety alerts. We do not sell your personal data to third parties.</p>
          </section>

          <section className="space-y-1">
            <h2 className="text-lg font-bold text-[var(--ny-text)]">3. Data Retention & Anonymization</h2>
            <p>Temporary session data is used to provide the feature you requested. Where the service stores account, booking, safety or support records, retention follows the applicable account and operational settings. Contact the team if you need more information about a specific record.</p>
          </section>

          <section className="space-y-1">
            <h2 className="text-lg font-bold text-[var(--ny-text)]">4. Contact Us</h2>
            <p>If you have questions about your data privacy or wish to request data erasure, use the <Link to="/contact" className="font-bold text-[var(--ny-green)] hover:underline">contact page</Link>. Do not include passwords or other sensitive information in a message.</p>
          </section>
        </div>
      </div>
    </ResponsiveContainer>
  )
}
