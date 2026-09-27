import { Link } from "react-router-dom"
import LegalPage, { LegalContact } from "../components/legal/LegalPage"

const sections = [
  {
    id: "using", title: "Using Nepal Yatra",
    body: <p>By using Nepal Yatra you agree to use it lawfully and to follow these terms. If you do not agree, please do not use the service. Our <Link className="ny-legal-link" to="/privacy-policy">Privacy Policy</Link> explains how personal information is handled.</p>,
  },
  {
    id: "information", title: "Travel information and its limits",
    body: (
      <>
        <p>We show tourism information from the sources available to us. Where coordinates, fares, opening hours or other details are not recorded, we say they are unavailable instead of guessing.</p>
        <p>Visa, permit, park and heritage fees are copied from the official pages we link to, with the date we checked them. Rules and fees change, so confirm them with the issuing authority before you travel.</p>
        <p>Places and services marked &quot;Unverified listing&quot; come from public data sources and have not been checked by our team.</p>
        <p>Weather, altitude and route estimates are approximate. Travel in the Himalaya carries real risk; use your own judgement and follow local guidance.</p>
      </>
    ),
  },
  {
    id: "assistant", title: "The travel assistant",
    body: <p>The chat assistant generates answers automatically and can be wrong. Do not rely on it for medical, legal, visa or safety decisions; check an official source or a qualified person.</p>,
  },
  {
    id: "emergency", title: "Emergency information",
    body: <p>The emergency page lists national hotlines and directory records where they are available. Nepal Yatra is not an emergency service and does not dispatch help. In a life-threatening emergency call the local authorities directly.</p>,
  },
  {
    id: "accounts", title: "Accounts",
    body: <p>Keep your sign-in details secure and tell us promptly if you think your account has been used without permission. We may suspend an account to protect other users, our records or the service. You can delete your account at any time on the <Link className="ny-legal-link" to="/data-deletion">data deletion page</Link>.</p>,
  },
  {
    id: "bookings", title: "Booking requests and payments",
    body: (
      <>
        <p>A booking request is a request for service, not a payment or a guaranteed reservation. No payment is taken on Nepal Yatra and card numbers are never accepted here.</p>
        <p>Where a price is shown, it comes from the provider&apos;s listing; confirm the final price with them before you travel. Payment, cancellation and refund arrangements are made directly with the hotel, operator or guide under their own terms.</p>
      </>
    ),
  },
  {
    id: "content", title: "What you submit",
    body: (
      <>
        <p>Reviews, place suggestions, photos and error reports must be accurate, lawful and yours to share. Spam, fake reviews, misleading coordinates and attempts to break or misuse the service are not allowed.</p>
        <p>By submitting content you confirm you have the right to share it and allow Nepal Yatra to display it on the service. Submissions are reviewed before they are published and may be edited for accuracy or declined. You can ask us to remove your content.</p>
      </>
    ),
  },
  {
    id: "third-parties", title: "Third-party services and content",
    body: (
      <>
        <p>Maps, photos, provider listings and some links come from other parties. Their availability, prices, policies and safety information remain their responsibility.</p>
        <p>Destination photos are shown under the licences given by their creators, with the source and licence listed where recorded. The maps use OpenStreetMap data, available under the Open Database License.</p>
      </>
    ),
  },
  {
    id: "changes", title: "Changes to the service and these terms",
    body: <p>We may change or stop features as the service develops. When we change these terms we update the date at the top; continuing to use the service after that means you accept the updated terms.</p>,
  },
  {
    id: "questions", title: "Questions and disputes",
    body: (
      <>
        <p>Please contact us first so we can understand the issue and keep an accurate record. Nothing in these terms limits rights you have under the law that applies to you.</p>
        <LegalContact />
      </>
    ),
  },
]

export default function TermsOfService() {
  return (
    <LegalPage
      pageKey="terms-of-service"
      title="Terms of Service"
      path="/terms-of-service"
      intro={<p>These terms cover how you may use Nepal Yatra, what our travel information can and cannot promise, and how booking requests work.</p>}
      sections={sections}
    />
  )
}
