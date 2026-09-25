import { FiFileText } from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { ResponsiveContainer } from "../components/common/ResponsiveSystem"
import CMSPageIntro from "../components/cms/CMSPageIntro"

export default function TermsOfService() {
  return (
    <ResponsiveContainer className="space-y-6 py-8">
      <Breadcrumbs items={[{ label: "Home", to: "/" }, { label: "Terms of Service", to: "/terms" }]} />
      <div className="ny-reading ny-card p-6 text-[var(--ny-text)] sm:p-8">
        <div>
          <span className="ny-kicker">Legal terms & conditions</span>
          <CMSPageIntro pageKey="terms-of-service" />
          <PageHeader title="Terms of Service" subtitle="A clear summary of how to use Nepal Yatra and the limits of the information it provides." icon={FiFileText} />
        </div>
        <div className="space-y-5 border-t border-[var(--ny-border)] pt-5 text-sm leading-7 text-[var(--ny-text-secondary)]">
          <section><h2 className="text-lg font-bold text-[var(--ny-text)]">1. Acceptance of terms</h2><p className="mt-1">By accessing or using Nepal Yatra, you agree to use the service lawfully and to follow these terms. If you do not agree, please do not use the service.</p></section>
          <section><h2 className="text-lg font-bold text-[var(--ny-text)]">2. Travel data and honesty</h2><p className="mt-1">The service displays recorded tourism information from the sources available to it. Where coordinates, fares or opening hours are unrecorded, they are marked as unavailable rather than replaced with a guess. Users must exercise personal judgment when travelling in high-altitude Himalayan regions.</p></section>
          <section><h2 className="text-lg font-bold text-[var(--ny-text)]">3. User conduct and submissions</h2><p className="mt-1">Place suggestions, reviews and error reports must be accurate, lawful and free from content you do not have the right to submit. Spam, fraudulent reviews, misleading coordinates and attempts to compromise the service are not permitted.</p></section>
          <section><h2 className="text-lg font-bold text-[var(--ny-text)]">4. Emergency information</h2><p className="mt-1">Emergency directory records may be shown when they are available. In a life-threatening emergency, contact the appropriate local authority immediately; Nepal Yatra does not replace emergency dispatch.</p></section>
          <section><h2 className="text-lg font-bold text-[var(--ny-text)]">5. Accounts</h2><p className="mt-1">Keep your sign-in details secure and tell us promptly if you believe an account has been used without permission. We may suspend an account when necessary to protect users, records or the service.</p></section>
          <section><h2 className="text-lg font-bold text-[var(--ny-text)]">6. Requests, payments and refunds</h2><p className="mt-1">A marketplace request is a request for service, not a payment or a guarantee of availability. Payment, cancellation, refund and booking arrangements are handled by the relevant provider under its own terms. Do not send card or password information through a feedback message.</p></section>
          <section><h2 className="text-lg font-bold text-[var(--ny-text)]">7. Third-party information</h2><p className="mt-1">Some links, maps, providers and directory records are operated by other parties. Their availability, prices, policies and safety information remain their responsibility. Confirm important details directly with the provider or local authority.</p></section>
          <section><h2 className="text-lg font-bold text-[var(--ny-text)]">8. Questions and disputes</h2><p className="mt-1">Contact the team first so we can understand the issue and keep an accurate record. These terms do not limit rights or remedies that may be available under applicable law.</p></section>
        </div>
      </div>
    </ResponsiveContainer>
  )
}
