"""
Payment Integration Module.

Provides a unified payment abstraction layer supporting multiple providers:
- Stripe (international cards)
- eSewa (Nepal's digital wallet)
- Khalti (Nepal's digital wallet)
- Cash on arrival

Each provider implements the same interface:
- create_payment(amount, currency, metadata) → payment intent
- verify_payment(payment_id) → payment status
- refund_payment(payment_id, amount) → refund status

Usage:
    from booking.payments import PaymentProcessor
    processor = PaymentProcessor(provider="stripe")
    payment = processor.create_payment(100.00, "USD", {"booking_id": 1})
"""

import hashlib
import hmac
import json
import logging
import uuid
from abc import ABC, abstractmethod
from decimal import Decimal

import requests
from django.conf import settings

logger = logging.getLogger(__name__)


class PaymentError(Exception):
    """Raised when a payment operation fails."""
    pass


class PaymentProvider(ABC):
    """Abstract base class for payment providers."""

    @abstractmethod
    def create_payment(self, amount, currency, metadata=None):
        """
        Create a payment intent/order.

        Args:
            amount: Payment amount as Decimal or float.
            currency: ISO 4217 currency code (e.g. "USD", "NPR").
            metadata: Optional dict of additional data (booking_id, etc.).

        Returns:
            dict with at least: payment_id, status, amount, currency,
            and provider-specific fields (client_secret, redirect_url, etc.)
        """
        pass

    @abstractmethod
    def verify_payment(self, payment_id):
        """
        Verify the status of a payment.

        Args:
            payment_id: The provider-specific payment identifier.

        Returns:
            dict with: payment_id, status, amount, currency, paid_at (optional)
        """
        pass

    @abstractmethod
    def refund_payment(self, payment_id, amount=None):
        """
        Refund a payment (full or partial).

        Args:
            payment_id: The provider-specific payment identifier.
            amount: Optional partial refund amount. None = full refund.

        Returns:
            dict with: refund_id, status, amount, payment_id
        """
        pass


class StripeProvider(PaymentProvider):
    """Stripe payment provider for international cards."""

    def __init__(self):
        self.api_key = getattr(settings, "STRIPE_SECRET_KEY", "")
        self.webhook_secret = getattr(settings, "STRIPE_WEBHOOK_SECRET", "")
        self.base_url = "https://api.stripe.com/v1"

    def _headers(self):
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

    def create_payment(self, amount, currency, metadata=None):
        if not self.api_key:
            raise PaymentError("Stripe is not configured (STRIPE_SECRET_KEY missing)")

        try:
            # Stripe expects amount in smallest currency unit (cents/paisa)
            amount_cents = int(Decimal(str(amount)) * 100)

            data = {
                "amount": amount_cents,
                "currency": currency.lower(),
                "automatic_payment_methods[enabled]": "true",
                "metadata": json.dumps(metadata or {}),
            }

            response = requests.post(
                f"{self.base_url}/payment_intents",
                data=data,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            return {
                "payment_id": result["id"],
                "status": result["status"],  # requires_payment_method, requires_confirmation, etc.
                "amount": amount,
                "currency": currency,
                "client_secret": result.get("client_secret"),
                "provider": "stripe",
            }
        except requests.RequestException as e:
            logger.error(f"Stripe create_payment failed: {e}")
            raise PaymentError(f"Failed to create Stripe payment: {e}")

    def verify_payment(self, payment_id):
        if not self.api_key:
            raise PaymentError("Stripe is not configured")

        try:
            response = requests.get(
                f"{self.base_url}/payment_intents/{payment_id}",
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            return {
                "payment_id": result["id"],
                "status": result["status"],  # succeeded, pending, failed, etc.
                "amount": Decimal(result["amount"]) / 100,
                "currency": result["currency"].upper(),
                "paid_at": result.get("charges", {}).get("data", [{}])[0].get("created"),
                "provider": "stripe",
            }
        except requests.RequestException as e:
            logger.error(f"Stripe verify_payment failed: {e}")
            raise PaymentError(f"Failed to verify Stripe payment: {e}")

    def refund_payment(self, payment_id, amount=None):
        if not self.api_key:
            raise PaymentError("Stripe is not configured")

        try:
            # First get the charge ID from the payment intent
            pi_response = requests.get(
                f"{self.base_url}/payment_intents/{payment_id}",
                headers=self._headers(),
                timeout=30,
            )
            pi_response.raise_for_status()
            pi_data = pi_response.json()

            charge_id = pi_data.get("charges", {}).get("data", [{}])[0].get("id")
            if not charge_id:
                raise PaymentError("No charge found for this payment intent")

            data = {"charge": charge_id}
            if amount:
                data["amount"] = int(Decimal(str(amount)) * 100)

            response = requests.post(
                f"{self.base_url}/refunds",
                data=data,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            return {
                "refund_id": result["id"],
                "status": result["status"],  # pending, succeeded, failed
                "amount": Decimal(result["amount"]) / 100,
                "payment_id": payment_id,
                "provider": "stripe",
            }
        except requests.RequestException as e:
            logger.error(f"Stripe refund_payment failed: {e}")
            raise PaymentError(f"Failed to refund Stripe payment: {e}")


class ESewaProvider(PaymentProvider):
    """eSewa payment provider (Nepal's digital wallet)."""

    def __init__(self):
        self.merchant_id = getattr(settings, "ESEWA_MERCHANT_ID", "")
        self.secret_key = getattr(settings, "ESEWA_SECRET_KEY", "")
        self.base_url = getattr(
            settings, "ESEWA_BASE_URL", "https://rc-epay.esewa.com.np"
        )

    def _generate_signature(self, data):
        """Generate HMAC-SHA256 signature for eSewa."""
        message = ",".join(f"{k}={v}" for k, v in sorted(data.items()))
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        return signature

    def create_payment(self, amount, currency, metadata=None):
        if not self.merchant_id or not self.secret_key:
            raise PaymentError("eSewa is not configured (ESEWA_MERCHANT_ID/ESEWA_SECRET_KEY missing)")

        transaction_id = str(uuid.uuid4())[:12]
        metadata = metadata or {}

        data = {
            "amt": str(amount),
            "pdc": "0",
            "psc": "0",
            "txAmt": "0",
            "tAmt": str(amount),
            "pid": transaction_id,
            "scd": self.merchant_id,
            "su": metadata.get("success_url", f"{settings.FRONTEND_URL}/payment/success"),
            "fu": metadata.get("failure_url", f"{settings.FRONTEND_URL}/payment/failure"),
        }

        # Generate signature
        signature_data = {
            "total_amount": data["tAmt"],
            "transaction_uuid": data["pid"],
            "product_code": data["scd"],
        }
        data["signature"] = self._generate_signature(signature_data)

        return {
            "payment_id": transaction_id,
            "status": "pending",
            "amount": amount,
            "currency": currency,
            "redirect_url": f"{self.base_url}/api/v2/epay/main/v2/form",
            "form_data": data,
            "provider": "esewa",
        }

    def verify_payment(self, payment_id):
        if not self.merchant_id or not self.secret_key:
            raise PaymentError("eSewa is not configured")

        try:
            # eSewa verification endpoint
            verify_url = f"{self.base_url}/api/v2/epay/transaction/status"
            params = {
                "product_code": self.merchant_id,
                "transaction_uuid": payment_id,
            }

            response = requests.get(verify_url, params=params, timeout=30)
            response.raise_for_status()
            result = response.json()

            return {
                "payment_id": payment_id,
                "status": result.get("status", "unknown").lower(),
                "amount": Decimal(result.get("total_amount", 0)),
                "currency": "NPR",
                "paid_at": result.get("date"),
                "provider": "esewa",
            }
        except requests.RequestException as e:
            logger.error(f"eSewa verify_payment failed: {e}")
            raise PaymentError(f"Failed to verify eSewa payment: {e}")

    def refund_payment(self, payment_id, amount=None):
        if not self.merchant_id or not self.secret_key:
            raise PaymentError("eSewa is not configured")

        try:
            refund_url = f"{self.base_url}/api/v2/epay/refund"
            data = {
                "product_code": self.merchant_id,
                "transaction_uuid": payment_id,
                "refund_amount": str(amount) if amount else "0",
            }

            response = requests.post(refund_url, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()

            return {
                "refund_id": result.get("refund_id", str(uuid.uuid4())),
                "status": result.get("status", "pending").lower(),
                "amount": amount,
                "payment_id": payment_id,
                "provider": "esewa",
            }
        except requests.RequestException as e:
            logger.error(f"eSewa refund_payment failed: {e}")
            raise PaymentError(f"Failed to refund eSewa payment: {e}")


class KhaltiProvider(PaymentProvider):
    """Khalti payment provider (Nepal's digital wallet)."""

    def __init__(self):
        self.secret_key = getattr(settings, "KHALTI_SECRET_KEY", "")
        self.base_url = getattr(
            settings, "KHALTI_BASE_URL", "https://khalti.com/api/v2"
        )

    def _headers(self):
        return {
            "Authorization": f"Key {self.secret_key}",
            "Content-Type": "application/json",
        }

    def create_payment(self, amount, currency, metadata=None):
        if not self.secret_key:
            raise PaymentError("Khalti is not configured (KHALTI_SECRET_KEY missing)")

        try:
            # Khalti expects amount in paisa (NPR)
            amount_paisa = int(Decimal(str(amount)) * 100)

            data = {
                "public_key": getattr(settings, "KHALTI_PUBLIC_KEY", ""),
                "mobile": metadata.get("phone", ""),
                "transaction_pin": metadata.get("pin", ""),
                "amount": amount_paisa,
                "product_identity": metadata.get("booking_id", str(uuid.uuid4())),
                "product_name": metadata.get("product_name", "Booking"),
                "product_url": metadata.get("product_url", settings.FRONTEND_URL),
            }

            response = requests.post(
                f"{self.base_url}/epayment/initiate/",
                json=data,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            return {
                "payment_id": result.get("idx"),
                "status": "pending",
                "amount": amount,
                "currency": currency,
                "redirect_url": result.get("payment_url"),
                "provider": "khalti",
            }
        except requests.RequestException as e:
            logger.error(f"Khalti create_payment failed: {e}")
            raise PaymentError(f"Failed to create Khalti payment: {e}")

    def verify_payment(self, payment_id):
        if not self.secret_key:
            raise PaymentError("Khalti is not configured")

        try:
            data = {
                "public_key": getattr(settings, "KHALTI_PUBLIC_KEY", ""),
                "idx": payment_id,
            }

            response = requests.post(
                f"{self.base_url}/epayment/lookup/",
                json=data,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            return {
                "payment_id": payment_id,
                "status": result.get("status", "unknown").lower(),
                "amount": Decimal(result.get("amount", 0)) / 100,
                "currency": "NPR",
                "paid_at": result.get("created_on"),
                "provider": "khalti",
            }
        except requests.RequestException as e:
            logger.error(f"Khalti verify_payment failed: {e}")
            raise PaymentError(f"Failed to verify Khalti payment: {e}")

    def refund_payment(self, payment_id, amount=None):
        if not self.secret_key:
            raise PaymentError("Khalti is not configured")

        try:
            data = {
                "public_key": getattr(settings, "KHALTI_PUBLIC_KEY", ""),
                "idx": payment_id,
                "amount": int(Decimal(str(amount)) * 100) if amount else None,
            }

            response = requests.post(
                f"{self.base_url}/epayment/refund/",
                json=data,
                headers=self._headers(),
                timeout=30,
            )
            response.raise_for_status()
            result = response.json()

            return {
                "refund_id": result.get("idx", str(uuid.uuid4())),
                "status": result.get("status", "pending").lower(),
                "amount": amount,
                "payment_id": payment_id,
                "provider": "khalti",
            }
        except requests.RequestException as e:
            logger.error(f"Khalti refund_payment failed: {e}")
            raise PaymentError(f"Failed to refund Khalti payment: {e}")


class CashOnArrivalProvider(PaymentProvider):
    """Cash on arrival payment provider (no online payment)."""

    def create_payment(self, amount, currency, metadata=None):
        return {
            "payment_id": f"COA-{uuid.uuid4().hex[:8].upper()}",
            "status": "pending",
            "amount": amount,
            "currency": currency,
            "instructions": "Pay in cash upon arrival at the destination.",
            "provider": "cash_on_arrival",
        }

    def verify_payment(self, payment_id):
        # Cash on arrival is verified manually by the hotel/staff
        return {
            "payment_id": payment_id,
            "status": "pending_manual_verification",
            "amount": None,
            "currency": None,
            "provider": "cash_on_arrival",
        }

    def refund_payment(self, payment_id, amount=None):
        # Cash on arrival refunds are handled manually
        return {
            "refund_id": f"REF-{uuid.uuid4().hex[:8].upper()}",
            "status": "manual_refund_required",
            "amount": amount,
            "payment_id": payment_id,
            "provider": "cash_on_arrival",
        }


# ---------------------------------------------------------------------------
# Payment Processor Factory
# ---------------------------------------------------------------------------

PROVIDERS = {
    "stripe": StripeProvider,
    "esewa": ESewaProvider,
    "khalti": KhaltiProvider,
    "cash_on_arrival": CashOnArrivalProvider,
}


class PaymentProcessor:
    """
    Unified payment processor that delegates to the appropriate provider.

    Usage:
        processor = PaymentProcessor("stripe")
        payment = processor.create_payment(100.00, "USD", {"booking_id": 1})
        status = processor.verify_payment(payment["payment_id"])
    """

    def __init__(self, provider_name):
        if provider_name not in PROVIDERS:
            raise PaymentError(
                f"Unknown payment provider: {provider_name}. "
                f"Available: {', '.join(PROVIDERS.keys())}"
            )
        self.provider_name = provider_name
        self.provider = PROVIDERS[provider_name]()

    def create_payment(self, amount, currency, metadata=None):
        return self.provider.create_payment(amount, currency, metadata)

    def verify_payment(self, payment_id):
        return self.provider.verify_payment(payment_id)

    def refund_payment(self, payment_id, amount=None):
        return self.provider.refund_payment(payment_id, amount)


def get_available_providers():
    """Return list of configured (available) payment providers."""
    available = []

    if getattr(settings, "STRIPE_SECRET_KEY", ""):
        available.append("stripe")
    if getattr(settings, "ESEWA_MERCHANT_ID", "") and getattr(settings, "ESEWA_SECRET_KEY", ""):
        available.append("esewa")
    if getattr(settings, "KHALTI_SECRET_KEY", ""):
        available.append("khalti")

    # Cash on arrival is always available
    available.append("cash_on_arrival")

    return available
