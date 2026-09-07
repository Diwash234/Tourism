import React from "react"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { ResponsiveContainer } from "../components/common/ResponsiveSystem"

export default function PrivacyPolicy() {
  return (
    <ResponsiveContainer className="py-8 space-y-6">
      <Breadcrumbs items={[
        { label: "Home", to: "/" },
        { label: "Privacy Policy", to: "/privacy" }
      ]} />

      <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200/80 space-y-6 text-slate-800">
        <div>
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-emerald-900 text-xs font-bold uppercase">
            Data Protection & Privacy
          </span>
          <h1 className="text-3xl font-black text-slate-900 mt-2">Privacy Policy</h1>
          <p className="text-xs text-slate-500">Last updated: August 2026 · Official Nepal Yatra Platform</p>
        </div>

        <div className="space-y-4 text-xs leading-relaxed text-slate-700 border-t border-slate-100 pt-4">
          <section className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">1. Information We Collect</h2>
            <p>We collect information you explicitly provide when creating an account, searching destinations, filing error reports, or submitting travel preferences. Geolocation data is requested only with your explicit browser consent.</p>
          </section>

          <section className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">2. How Data is Used</h2>
            <p>Your preferences and interaction signals are used to generate personalized recommendations, calculate real-time travel routes, and deliver safety alerts. We do not sell your personal data to third parties.</p>
          </section>

          <section className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">3. Data Retention & Anonymization</h2>
            <p>Temporary session data is subject to automated retention policies. Essential booking receipts, active emergency advisories, and administrative audit logs are retained securely in accordance with Nepal data protection guidelines.</p>
          </section>

          <section className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">4. Contact Us</h2>
            <p>If you have questions about your data privacy or wish to request data erasure, contact our Data Protection Desk at <a href="mailto:privacy@nepalyatra.gov.np" className="text-emerald-700 font-bold hover:underline">privacy@nepalyatra.gov.np</a>.</p>
          </section>
        </div>
      </div>
    </ResponsiveContainer>
  )
}
