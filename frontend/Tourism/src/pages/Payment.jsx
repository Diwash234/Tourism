import { useState, useCallback, useMemo } from "react"
import { motion } from "framer-motion"
import {
  FiCreditCard, FiCheck, FiX, FiDownload, FiShield,
  FiClock, FiAlertCircle, FiSmartphone, FiDollarSign,
} from "react-icons/fi"
import PageHeader from "../components/common/PageHeader"
import Loader from "../components/common/Loader"
import useToast from "../hooks/useToast"

// ─── Payment Method Config ───────────────────────────────────────────────────
const PAYMENT_METHODS = [
  { id: "stripe", label: "Stripe", icon: FiCreditCard, description: "Credit/Debit Card" },
  { id: "esewa", label: "eSewa", icon: FiSmartphone, description: "Digital Wallet" },
  { id: "khalti", label: "Khalti", icon: FiSmartphone, description: "Digital Wallet" },
  { id: "cash", label: "Cash on Arrival", icon: FiDollarSign, description: "Pay at destination" },
]

// ─── Booking Summary Data (simulated) ────────────────────────────────────────
const BOOKING_SUMMARY = {
  destination: "Pokhara - 3 Nights",
  hotel: "Himalaya Resort & Spa",
  checkIn: "2026-10-15",
  checkOut: "2026-10-18",
  guests: 2,
  rooms: 1,
  pricePerNight: 8500,
  subtotal: 25500,
  taxes: 3315,
  discount: 2550,
  total: 26265,
  currency: "NPR",
}

// ─── Progress Steps ──────────────────────────────────────────────────────────
const PAYMENT_STEPS = ["Review", "Payment", "Confirmation"]

// ─── Card Input Component ────────────────────────────────────────────────────
const CardInput = ({ label, placeholder, value, onChange, maxLength, type = "text" }) => (
  <div>
    <label className="block text-xs font-medium text-gray-500 mb-1">{label}</label>
    <input
      type={type}
      placeholder={placeholder}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      maxLength={maxLength}
      className="input-field w-full"
    />
  </div>
)

// ─── Success Receipt Component ───────────────────────────────────────────────
const Receipt = ({ booking, onClose }) => {
  const handleDownload = useCallback(() => {
    const receiptContent = `
PAYMENT RECEIPT
================
Booking Reference: ${booking.reference}
Date: ${new Date().toLocaleDateString()}
Destination: ${booking.destination}
Hotel: ${booking.hotel}
Check-in: ${booking.checkIn}
Check-out: ${booking.checkOut}
Guests: ${booking.guests}
Total Paid: ${booking.currency} ${booking.total.toLocaleString()}
Payment Method: ${booking.method}
Status: CONFIRMED
    `.trim()
    const blob = new Blob([receiptContent], { type: "text/plain" })
    const link = document.createElement("a")
    link.href = URL.createObjectURL(blob)
    link.download = `receipt-${booking.reference}.txt`
    link.click()
    URL.revokeObjectURL(link.href)
  }, [booking])

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="text-center py-8"
    >
      <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
        <FiCheck size={40} className="text-emerald-600" />
      </div>
      <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h2>
      <p className="text-gray-500 mb-6">Your booking has been confirmed. A confirmation email has been sent to your registered email address.</p>

      <div className="card-base p-6 max-w-md mx-auto text-left space-y-3">
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Reference</span>
          <span className="text-sm font-mono font-bold">{booking.reference}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Destination</span>
          <span className="text-sm font-medium">{booking.destination}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Hotel</span>
          <span className="text-sm font-medium">{booking.hotel}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Check-in</span>
          <span className="text-sm font-medium">{booking.checkIn}</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-gray-500">Check-out</span>
          <span className="text-sm font-medium">{booking.checkOut}</span>
        </div>
        <hr className="border-gray-100" />
        <div className="flex justify-between">
          <span className="text-sm font-semibold text-gray-900">Total Paid</span>
          <span className="text-lg font-bold text-emerald-600">{booking.currency} {booking.total.toLocaleString()}</span>
        </div>
      </div>

      <div className="flex items-center justify-center gap-3 mt-6">
        <button onClick={handleDownload} className="btn-primary flex items-center gap-2">
          <FiDownload size={16} /> Download Receipt
        </button>
        <button onClick={onClose} className="btn-secondary">
          Done
        </button>
      </div>
    </motion.div>
  )
}

// ─── Main Payment Page ───────────────────────────────────────────────────────
const Payment = () => {
  const { showToast } = useToast()
  const [step, setStep] = useState(0)
  const [paymentMethod, setPaymentMethod] = useState("stripe")
  const [processing, setProcessing] = useState(false)
  const [paymentStatus, setPaymentStatus] = useState(null) // null | 'success' | 'failed'
  const [cardData, setCardData] = useState({
    number: "",
    name: "",
    expiry: "",
    cvv: "",
  })
  const [walletId, setWalletId] = useState("")
  // Booking reference is generated once when payment succeeds (in the handler),
  // so no Date.now() runs during render (react-hooks/purity).
  const [bookingReference, setBookingReference] = useState("")

  const selectedMethod = useMemo(
    () => PAYMENT_METHODS.find((m) => m.id === paymentMethod),
    [paymentMethod]
  )

  const handleCardChange = useCallback((field, value) => {
    setCardData((prev) => ({ ...prev, [field]: value }))
  }, [])

  const handlePayment = useCallback(async () => {
    setProcessing(true)
    setStep(1)

    // Simulate payment processing
    await new Promise((resolve) => setTimeout(resolve, 2500))

    // Simulate success/failure (90% success rate)
    const success = Math.random() > 0.1
    setProcessing(false)

    if (success) {
      setBookingReference(`NYP-${Date.now().toString(36).toUpperCase()}`)
      setPaymentStatus("success")
      setStep(2)
      showToast("Payment successful! Booking confirmed.", "success")
    } else {
      setPaymentStatus("failed")
      showToast("Payment failed. Please try again.", "error")
    }
  }, [showToast])

  const handleRetry = useCallback(() => {
    setPaymentStatus(null)
    setStep(0)
  }, [])

  const handleNewBooking = useCallback(() => {
    setPaymentStatus(null)
    setStep(0)
    setCardData({ number: "", name: "", expiry: "", cvv: "" })
    setWalletId("")
  }, [])

  // ─── Render: Success State ──────────────────────────────────────────────
  if (paymentStatus === "success") {
    return (
      <div className="ny-page mx-auto w-full max-w-2xl">
        <Receipt
          booking={{
            reference: bookingReference,
            ...BOOKING_SUMMARY,
            method: selectedMethod?.label,
          }}
          onClose={handleNewBooking}
        />
      </div>
    )
  }

  // ─── Render: Failure State ──────────────────────────────────────────────
  if (paymentStatus === "failed") {
    return (
      <div className="ny-page mx-auto w-full max-w-2xl">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card-base p-8 text-center"
        >
          <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <FiX size={40} className="text-red-500" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Payment Failed</h2>
          <p className="text-gray-500 mb-6">We couldn't process your payment. Please check your details and try again.</p>
          <div className="flex items-center justify-center gap-3">
            <button onClick={handleRetry} className="btn-primary">
              Try Again
            </button>
            <button onClick={handleNewBooking} className="btn-secondary">
              Cancel
            </button>
          </div>
        </motion.div>
      </div>
    )
  }

  // ─── Render: Payment Form ───────────────────────────────────────────────
  return (
    <div className="ny-page mx-auto w-full max-w-4xl space-y-6">
      <PageHeader
        title="Complete Your Booking"
        subtitle="Review your booking details and choose a payment method."
        icon={FiCreditCard}
      />

      {/* Progress Steps */}
      <div className="flex items-center justify-center gap-4">
        {PAYMENT_STEPS.map((label, i) => (
          <div key={label} className="flex items-center gap-2">
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${
                i <= step ? "bg-emerald-600 text-white" : "bg-gray-200 text-gray-500"
              }`}
            >
              {i < step ? <FiCheck size={16} /> : i + 1}
            </div>
            <span className={`text-sm font-medium ${i <= step ? "text-emerald-700" : "text-gray-400"}`}>
              {label}
            </span>
            {i < PAYMENT_STEPS.length - 1 && (
              <div className={`w-12 h-0.5 ${i < step ? "bg-emerald-600" : "bg-gray-200"}`} />
            )}
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Booking Summary */}
        <div className="lg:col-span-1">
          <div className="card-base p-5 sticky top-4">
            <h3 className="font-semibold text-gray-900 mb-4">Booking Summary</h3>
            <div className="space-y-3 text-sm">
              <div>
                <p className="text-gray-500">Destination</p>
                <p className="font-medium text-gray-900">{BOOKING_SUMMARY.destination}</p>
              </div>
              <div>
                <p className="text-gray-500">Hotel</p>
                <p className="font-medium text-gray-900">{BOOKING_SUMMARY.hotel}</p>
              </div>
              <div className="flex justify-between">
                <div>
                  <p className="text-gray-500">Check-in</p>
                  <p className="font-medium">{BOOKING_SUMMARY.checkIn}</p>
                </div>
                <div className="text-right">
                  <p className="text-gray-500">Check-out</p>
                  <p className="font-medium">{BOOKING_SUMMARY.checkOut}</p>
                </div>
              </div>
              <div className="flex justify-between">
                <div>
                  <p className="text-gray-500">Guests</p>
                  <p className="font-medium">{BOOKING_SUMMARY.guests}</p>
                </div>
                <div className="text-right">
                  <p className="text-gray-500">Rooms</p>
                  <p className="font-medium">{BOOKING_SUMMARY.rooms}</p>
                </div>
              </div>
              <hr className="border-gray-100" />
              <div className="space-y-1">
                <div className="flex justify-between text-gray-600">
                  <span>{BOOKING_SUMMARY.pricePerNight.toLocaleString()} x {BOOKING_SUMMARY.guests} nights</span>
                  <span>{BOOKING_SUMMARY.subtotal.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-gray-600">
                  <span>Taxes & fees</span>
                  <span>{BOOKING_SUMMARY.taxes.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-emerald-600">
                  <span>Discount</span>
                  <span>-{BOOKING_SUMMARY.discount.toLocaleString()}</span>
                </div>
              </div>
              <hr className="border-gray-100" />
              <div className="flex justify-between items-center">
                <span className="font-semibold text-gray-900">Total</span>
                <span className="text-xl font-bold text-emerald-600">
                  {BOOKING_SUMMARY.currency} {BOOKING_SUMMARY.total.toLocaleString()}
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Payment Form */}
        <div className="lg:col-span-2 space-y-6">
          {/* Payment Method Selector */}
          <div className="card-base p-5">
            <h3 className="font-semibold text-gray-900 mb-4">Payment Method</h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {PAYMENT_METHODS.map((method) => {
                const Icon = method.icon
                return (
                  <button
                    key={method.id}
                    type="button"
                    onClick={() => setPaymentMethod(method.id)}
                    className={`p-4 rounded-xl border-2 text-center transition-all ${
                      paymentMethod === method.id
                        ? "border-emerald-500 bg-emerald-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}
                  >
                    <Icon size={24} className={`mx-auto mb-2 ${paymentMethod === method.id ? "text-emerald-600" : "text-gray-400"}`} />
                    <p className="text-sm font-medium text-gray-900">{method.label}</p>
                    <p className="text-xs text-gray-500">{method.description}</p>
                  </button>
                )
              })}
            </div>
          </div>

          {/* Card Form (Stripe) */}
          {paymentMethod === "stripe" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card-base p-5"
            >
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <FiCreditCard size={18} /> Card Details
              </h3>
              <div className="space-y-4">
                <CardInput
                  label="Card Number"
                  placeholder="4242 4242 4242 4242"
                  value={cardData.number}
                  onChange={(v) => handleCardChange("number", v)}
                  maxLength={19}
                />
                <CardInput
                  label="Cardholder Name"
                  placeholder="John Doe"
                  value={cardData.name}
                  onChange={(v) => handleCardChange("name", v)}
                />
                <div className="grid grid-cols-2 gap-4">
                  <CardInput
                    label="Expiry Date"
                    placeholder="MM/YY"
                    value={cardData.expiry}
                    onChange={(v) => handleCardChange("expiry", v)}
                    maxLength={5}
                  />
                  <CardInput
                    label="CVV"
                    placeholder="123"
                    value={cardData.cvv}
                    onChange={(v) => handleCardChange("cvv", v)}
                    maxLength={4}
                    type="password"
                  />
                </div>
              </div>
            </motion.div>
          )}

          {/* eSewa / Khalti Redirect Simulation */}
          {(paymentMethod === "esewa" || paymentMethod === "khalti") && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card-base p-5"
            >
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <FiSmartphone size={18} /> {selectedMethod.label} Payment
              </h3>
              <div className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-gray-500 mb-1">
                    {selectedMethod.label} ID / Mobile Number
                  </label>
                  <input
                    type="text"
                    placeholder="98XXXXXXXX"
                    value={walletId}
                    onChange={(e) => setWalletId(e.target.value)}
                    className="input-field w-full"
                    maxLength={10}
                  />
                </div>
                <div className="p-4 bg-blue-50 rounded-xl text-sm text-blue-800">
                  <p className="flex items-center gap-2">
                    <FiShield size={16} />
                    You will be redirected to {selectedMethod.label} to complete the payment securely.
                  </p>
                </div>
              </div>
            </motion.div>
          )}

          {/* Cash on Arrival */}
          {paymentMethod === "cash" && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="card-base p-5"
            >
              <h3 className="font-semibold text-gray-900 mb-4 flex items-center gap-2">
                <FiDollarSign size={18} /> Cash on Arrival
              </h3>
              <div className="p-4 bg-amber-50 rounded-xl text-sm text-amber-800 space-y-2">
                <p className="flex items-center gap-2">
                  <FiAlertCircle size={16} />
                  Please prepare the exact amount in Nepali Rupees (NPR).
                </p>
                <p className="flex items-center gap-2">
                  <FiClock size={16} />
                  Payment is due at check-in. Your booking will be held for 24 hours.
                </p>
              </div>
            </motion.div>
          )}

          {/* Security Notice */}
          <div className="flex items-center gap-2 text-xs text-gray-500 px-1">
            <FiShield size={14} className="text-emerald-500" />
            <span>Your payment information is encrypted and secure. We never store your card details.</span>
          </div>

          {/* Pay Button */}
          <button
            onClick={handlePayment}
            disabled={processing}
            className="w-full btn-primary py-4 text-lg font-bold flex items-center justify-center gap-2"
          >
            {processing ? (
              <>
                <Loader size="sm" /> Processing...
              </>
            ) : (
              <>
                <FiShield size={18} />
                Pay {BOOKING_SUMMARY.currency} {BOOKING_SUMMARY.total.toLocaleString()}
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}

export default Payment
