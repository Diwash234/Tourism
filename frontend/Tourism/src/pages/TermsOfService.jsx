import React from "react"
import Breadcrumbs from "../components/common/Breadcrumbs"
import { ResponsiveContainer } from "../components/common/ResponsiveSystem"

export default function TermsOfService() {
  return (
    <ResponsiveContainer className="py-8 space-y-6">
      <Breadcrumbs items={[
        { label: "Home", to: "/" },
        { label: "Terms of Service", to: "/terms" }
      ]} />

      <div className="bg-white rounded-3xl p-8 shadow-sm border border-slate-200/80 space-y-6 text-slate-800">
        <div>
          <span className="px-3 py-1 rounded-full bg-emerald-100 text-[#102A2E] text-xs font-bold uppercase">
            Legal Terms & Conditions
          </span>
          <h1 className="text-3xl font-black text-slate-900 mt-2">Terms of Service</h1>
          <p className="text-xs text-slate-500">Effective Date: August 2026 · Official Nepal Yatra Platform</p>
        </div>

        <div className="space-y-4 text-xs leading-relaxed text-slate-700 border-t border-slate-100 pt-4">
          <section className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">1. Acceptance of Terms</h2>
            <p>By accessing or using the Nepal Yatra platform, you agree to comply with and be bound by these Terms of Service. If you do not agree, please do not use our services.</p>
          </section>

          <section className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">2. Travel Data & Honesty Policy</h2>
            <p>Our platform displays verified tourism data from official administrative registries. Where coordinates, fares, or opening hours are unrecorded, they are marked as "Not recorded" or "Route unavailable". Users must exercise personal judgment when traveling in high-altitude Himalayan regions.</p>
          </section>

          <section className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">3. User Conduct & Submissions</h2>
            <p>Users submitting place suggestions, hotel reviews, or error reports guarantee that their submissions are accurate and free from copyright infringement. Spam, fraudulent reviews, or misleading coordinates are strictly prohibited.</p>
          </section>

          <section className="space-y-1">
            <h2 className="text-base font-bold text-slate-900">4. Emergency & Helplines</h2>
            <p>Emergency directory numbers (Tourist Police 1144, Nepal Police 100, Ambulance 102) are provided for traveler safety. In life-threatening emergencies, contact local authorities immediately.</p>
          </section>
        </div>
      </div>
    </ResponsiveContainer>
  )
}
