import { Link } from "react-router-dom"
import LegalPage, { LegalContact, LegalTable } from "../components/legal/LegalPage"

// Written from what the code actually stores and sends (models, settings and
// integrations as of the date shown). If a feature or provider changes,
// update this page in the same change.
const sections = [
  {
    id: "what-we-collect", title: "What we collect",
    body: (
      <>
        <p>You can browse destinations, maps, travel rules and emergency numbers without an account. We only store personal information when you give it to us or use a feature that needs it:</p>
        <LegalTable head={["Information", "When", "Why"]} rows={[
          ["Email, name, password (stored hashed)", "You create an account", "To sign you in and contact you about your account"],
          ["Google or GitHub account ID", "You sign in with Google or GitHub", "To link that sign-in to your account"],
          ["Phone number (optional)", "You add it to your profile", "To verify it by SMS code and for safety contacts"],
          ["Profile photo, bio, city and country (optional)", "You add them", "To show your profile"],
          ["Location (latitude and longitude)", "You allow location in your browser, or set a place yourself", "To find places, services and help near you"],
          ["Trip plans, favourites, visit history, saved routes and budgets", "You save them", "To keep your plans between visits"],
          ["Booking requests (name, email, phone, dates, party size)", "You request a hotel, package or guide", "To pass your request to the provider and show its status"],
          ["Companion and document details (name, relation, phone, ID type and number, nationality, notes)", "You add them on Personal details", "So they are ready when you plan or book a trip"],
          ["Trusted contacts and live trip location", "You turn on trip sharing or send an SOS", "To let the people you chose see where you are and to raise an alert"],
          ["Messages to the travel assistant", "You use the chat", "To answer your question and keep the conversation"],
          ["Reviews, place or service suggestions, photos, feedback and support messages", "You submit them", "To review, publish or answer them"],
          ["Newsletter email address", "You subscribe in the footer", "To send occasional travel notes"],
          ["Push notification token", "You allow notifications", "To send alerts to your device"],
        ]} />
        <p>We do not ask for your date of birth, gender or home address, and we never ask for card numbers: no payment is taken on this site.</p>
      </>
    ),
  },
  {
    id: "automatic", title: "Information collected automatically",
    body: (
      <>
        <p>Like most websites, our server logs requests. Security and audit logs record the time, the action, your account (if signed in), your IP address and browser type, so we can investigate misuse and errors.</p>
        <p>If a page needs your approximate location and your browser has not shared it (for example a nearby search without location permission), the site may look up your IP address with an operator-configured HTTPS GeoIP service to estimate your city. This is disabled unless the site operator configures that secure service, happens only for that request, and never runs for private network addresses.</p>
        <p>We do not use analytics, advertising or tracking cookies, and we do not build advertising profiles. See the <Link className="ny-legal-link" to="/cookie-policy">Cookie Policy</Link> for what is stored in your browser.</p>
      </>
    ),
  },
  {
    id: "use", title: "How we use information",
    body: (
      <ul className="list-disc space-y-1 pl-5">
        <li>To provide the features you use: accounts, trip planning, booking requests, safety sharing, chat and notifications.</li>
        <li>To suggest destinations based on your stated interests, month and starting point, and on places you saved or viewed.</li>
        <li>To review and publish content that people submit, and to answer support requests.</li>
        <li>To keep the service secure, find errors and prevent abuse.</li>
        <li>To send the newsletter, only if you subscribed. Any newsletter we send includes a personal unsubscribe link, and you can also unsubscribe on the <Link className="ny-legal-link" to="/unsubscribe">unsubscribe page</Link>.</li>
      </ul>
    ),
  },
  {
    id: "sharing", title: "Who receives your information",
    body: (
      <>
        <p>We do not sell personal information. We share it only as described here.</p>
        <p><strong className="text-[var(--ny-text)]">Providers you request.</strong> When you send a booking request, the hotel, package operator or guide receives the details in that request.</p>
        <p><strong className="text-[var(--ny-text)]">People you choose.</strong> Trusted contacts can see a trip you share with them, until the link expires or you stop sharing. Anyone with a shared trip-plan link can read that plan; your name, email and notes are removed from it.</p>
        <p><strong className="text-[var(--ny-text)]">Services that run parts of the site.</strong> Some features only work when the site operator has switched on the matching service:</p>
        <LegalTable head={["Service", "Used for", "What it receives"]} rows={[
          ["OpenStreetMap tile servers; Esri (satellite layer)", "Map images", "Your IP address and the map area you view (sent by your browser)"],
          ["Wikimedia Commons", "Destination photos", "Your IP address when your browser loads a photo"],
          ["YouTube (privacy-enhanced mode)", "Videos placed on some pages", "Your IP address when you play a video"],
          ["Google or GitHub", "Optional sign-in", "The sign-in request you start"],
          ["Email provider (SMTP)", "Account and booking emails", "Your email address and the message"],
          ["Twilio", "SMS verification codes", "Your phone number and the code"],
          ["Firebase Cloud Messaging (Google)", "Push notifications", "Your device token and the notification"],
          ["OpenAI, Google Gemini or Groq", "The travel assistant, when enabled", "The messages you type in the chat"],
          ["Google Cloud Translation", "The translation tool, when enabled", "The text you ask to translate"],
          ["Configured HTTPS GeoIP provider", "Approximate location without GPS", "Your IP address, only when the operator enables it (see above)"],
          ["OpenStreetMap Nominatim and Overpass; a routing (OSRM) server", "Place search, nearby places, routes", "The place names or coordinates of the search"],
        ]} />
        <p>Weather, exchange rates and elevation are fetched for destination coordinates only, not for you.</p>
        <p><strong className="text-[var(--ny-text)]">Legal reasons.</strong> We may disclose information if the law requires it, or to protect someone&apos;s safety.</p>
      </>
    ),
  },
  {
    id: "retention", title: "How long we keep it",
    body: (
      <>
        <LegalTable head={["Record", "Kept"]} rows={[
          ["Account, plans, favourites, budgets, documents, contacts, chat conversations", "Until you delete them or your account"],
          ["Live trip location points", "30 days"],
          ["Read notifications", "365 days"],
          ["Recommendation activity", "365 days"],
          ["Resolved SOS alerts", "730 days, for safety follow-up"],
          ["Routine audit logs", "2,555 days (about 7 years); security warnings and errors are kept longer"],
          ["Booking requests", "Not deleted automatically at present. If you delete your account, your name, email, phone and notes are removed from them"],
          ["Newsletter address", "Until you unsubscribe"],
        ]} />
        <p>These are the default periods. Administrators can adjust them within fixed limits. Deleted records may remain in server backups until those backups are replaced.</p>
      </>
    ),
  },
  {
    id: "choices", title: "Your choices and rights",
    body: (
      <>
        <ul className="list-disc space-y-1 pl-5">
          <li>View and correct your details on your <Link className="ny-legal-link" to="/profile">profile</Link> and <Link className="ny-legal-link" to="/personal-details">personal details</Link> pages.</li>
          <li>Delete your account yourself on the <Link className="ny-legal-link" to="/data-deletion">data deletion page</Link>.</li>
          <li><Link className="ny-legal-link" to="/unsubscribe">Unsubscribe</Link> from the newsletter at any time.</li>
          <li>Turn off location or notification permission in your browser or device settings.</li>
          <li>Ask us for a copy of your information, or ask a question about how it is used, through the contact details below.</li>
        </ul>
        <p>Depending on where you live, local law may give you further rights. Contact us and we will respond.</p>
      </>
    ),
  },
  {
    id: "security", title: "Security",
    body: <p>Passwords are stored as one-way hashes, sign-in uses expiring tokens, and staff access is limited by role and logged. No system is perfectly secure, so please use a unique password and tell us if you think your account has been misused.</p>,
  },
  {
    id: "children", title: "Children",
    body: <p>Nepal Yatra is meant for adults planning travel. If you believe a child has created an account, contact us and we will delete it.</p>,
  },
  {
    id: "changes", title: "Changes to this policy",
    body: <p>When we change this policy we update the date at the top. If a change affects how we use information you already gave us, we will say so on the site before it applies.</p>,
  },
  { id: "contact", title: "Contact", body: <LegalContact /> },
]

export default function PrivacyPolicy() {
  return (
    <LegalPage
      pageKey="privacy-policy"
      title="Privacy Policy"
      path="/privacy-policy"
      intro={<p>This policy explains what personal information Nepal Yatra stores, why, which outside services receive it, how long it is kept and how you can delete it.</p>}
      sections={sections}
    />
  )
}
