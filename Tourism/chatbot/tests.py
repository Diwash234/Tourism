from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from tourist.models import User
from .models import ChatConversation, ChatMessage


class ChatbotTests(APITestCase):
    def test_anonymous_user_can_start_conversation(self):
        response = self.client.post(reverse("chatbot-message"), {"message": "What's the weather in Pokhara?"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("reply", response.data)
        self.assertIn("conversation_id", response.data)
        # No OPENAI_API_KEY configured in tests -> graceful fallback message, not an error.
        self.assertIn("isn't configured", response.data["reply"])

    def test_conversation_persists_messages(self):
        response = self.client.post(reverse("chatbot-message"), {"message": "Hello"})
        conversation_id = response.data["conversation_id"]
        conversation = ChatConversation.objects.get(id=conversation_id)
        self.assertEqual(conversation.messages.count(), 2)  # user message + assistant reply
        self.assertEqual(conversation.messages.first().role, ChatMessage.Role.USER)

    def test_continuing_a_conversation_reuses_it(self):
        first = self.client.post(reverse("chatbot-message"), {"message": "Hi"})
        conversation_id = first.data["conversation_id"]
        second = self.client.post(reverse("chatbot-message"), {
            "message": "Tell me more", "conversation_id": conversation_id,
        })
        self.assertEqual(second.data["conversation_id"], conversation_id)
        conversation = ChatConversation.objects.get(id=conversation_id)
        self.assertEqual(conversation.messages.count(), 4)

    def test_authenticated_user_history(self):
        user = User.objects.create_user(email="chatter@example.com", password="Pass123!", is_verified=True)
        self.client.force_authenticate(user=user)
        self.client.post(reverse("chatbot-message"), {"message": "Hello"})

        response = self.client.get(reverse("chatbot-history"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_history_requires_auth(self):
        response = self.client.get(reverse("chatbot-history"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_package_question_uses_published_marketplace(self):
        from tourist.models import MarketplaceListing, MarketplacePartner
        partner = MarketplacePartner.objects.create(
            name="Lakeside Lodge", kind="hotel", email="lodge@example.com", status="approved",
        )
        MarketplaceListing.objects.create(
            partner=partner, title="Phewa Weekend Stay", kind="package",
            summary="Two nights", price_npr="12000.00", status="published",
        )
        MarketplaceListing.objects.create(
            partner=partner, title="Hidden Draft", price_npr="1.00", status="draft",
        )
        response = self.client.post(reverse("chatbot-message"), {"message": "What travel packages can I add to a trip?"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Phewa Weekend Stay", response.data["reply"])
        self.assertNotIn("Hidden Draft", response.data["reply"])
        titles = [row["title"] for row in response.data.get("package_cards", [])]
        self.assertIn("Phewa Weekend Stay", titles)
        self.assertNotIn("Hidden Draft", titles)

    def test_budget_trip_matches_published_listing(self):
        from tourist.models import MarketplaceListing, MarketplacePartner
        partner = MarketplacePartner.objects.create(
            name="Budget Treks", kind="operator", email="budget@example.com", status="approved",
        )
        MarketplaceListing.objects.create(
            partner=partner, title="Five Day Nepal Circuit", kind="package",
            summary="Kathmandu and Pokhara", price_npr="50000.00", duration_days=5, status="published",
        )
        MarketplaceListing.objects.create(
            partner=partner, title="Luxury Over Budget", kind="package",
            summary="Too expensive", price_npr="200000.00", duration_days=5, status="published",
        )
        MarketplaceListing.objects.create(
            partner=partner, title="Unpublished Bargain", kind="package",
            summary="Hidden", price_npr="10000.00", duration_days=5, status="pending",
        )
        response = self.client.post(reverse("chatbot-message"), {
            "message": "I want a 5-day trip to Nepal under $500",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("Five Day Nepal Circuit", response.data["reply"])
        self.assertNotIn("Luxury Over Budget", response.data["reply"])
        self.assertNotIn("Unpublished Bargain", response.data["reply"])
        titles = [row["title"] for row in response.data.get("package_cards", [])]
        self.assertIn("Five Day Nepal Circuit", titles)
        self.assertNotIn("Luxury Over Budget", titles)
        self.assertNotIn("Unpublished Bargain", titles)
        self.assertFalse(any(row.get("is_alternative") for row in response.data.get("package_cards", []) if row["title"] == "Five Day Nepal Circuit"))

    def test_wrong_duration_is_not_a_primary_match(self):
        from tourist.models import MarketplaceListing, MarketplacePartner
        partner = MarketplacePartner.objects.create(
            name="Duration Treks", kind="operator", email="duration@example.com", status="approved",
        )
        MarketplaceListing.objects.create(
            partner=partner, title="Five Day Nepal Circuit", kind="package",
            summary="Kathmandu and Pokhara", price_npr="50000.00", duration_days=5, status="published",
        )
        MarketplaceListing.objects.create(
            partner=partner, title="Twelve Day Circuit", kind="package",
            summary="Long trek", price_npr="40000.00", duration_days=12, status="published",
        )
        MarketplaceListing.objects.create(
            partner=partner, title="Six Day Nearby", kind="package",
            summary="Almost five", price_npr="45000.00", duration_days=6, status="published",
        )
        response = self.client.post(reverse("chatbot-message"), {
            "message": "I want a 5-day trip to Nepal under $500",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cards = response.data.get("package_cards", [])
        by_title = {row["title"]: row for row in cards}
        self.assertIn("Five Day Nepal Circuit", by_title)
        self.assertFalse(by_title["Five Day Nepal Circuit"].get("is_alternative"))
        self.assertNotIn("Twelve Day Circuit", by_title)
        self.assertNotIn("Twelve Day Circuit", response.data["reply"])
        if "Six Day Nearby" in by_title:
            self.assertTrue(by_title["Six Day Nearby"].get("is_alternative"))

    def test_suspended_partner_and_pending_listing_are_excluded(self):
        from tourist.models import MarketplaceListing, MarketplacePartner
        suspended = MarketplacePartner.objects.create(
            name="Suspended Treks", kind="operator", email="susp@example.com", status="suspended",
        )
        approved = MarketplacePartner.objects.create(
            name="Live Treks", kind="operator", email="live@example.com", status="approved",
        )
        MarketplaceListing.objects.create(
            partner=suspended, title="Suspended Five Day", price_npr="10000.00",
            duration_days=5, status="published",
        )
        MarketplaceListing.objects.create(
            partner=approved, title="Archived Five Day", price_npr="10000.00",
            duration_days=5, status="archived",
        )
        MarketplaceListing.objects.create(
            partner=approved, title="Pending Five Day", price_npr="10000.00",
            duration_days=5, status="pending",
        )
        response = self.client.post(reverse("chatbot-message"), {
            "message": "I want a 5-day trip to Nepal under $500",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("I couldn't find a published package matching those requirements right now.", response.data["reply"])
        self.assertNotIn("Suspended Five Day", response.data["reply"])
        self.assertNotIn("Invented Himalayan Special", response.data["reply"])
        titles = [row["title"] for row in response.data.get("package_cards", [])]
        self.assertEqual(titles, [])

    def test_emergency_cards_do_not_invent_hospital_phones(self):
        from tourist.models import Category, Destination, Hospital
        category = Category.objects.create(name="Chat Emergency")
        dest = Destination.objects.create(
            name="Chat Valley", category=category, description="Test",
            latitude=28.2, longitude=83.9, status="approved", is_active=True,
        )
        Hospital.objects.create(
            destination=dest, name="Silent Clinic", address="Ward 1",
            phone="", latitude=28.2, longitude=83.9, district="Kaski",
        )
        response = self.client.post(reverse("chatbot-message"), {"message": "nearest hospital emergency"})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn("4412404", response.data["reply"])
        self.assertNotIn("4424111", response.data["reply"])
        cards = response.data.get("emergency_cards", [])
        self.assertTrue(cards)
        for card in cards:
            self.assertNotIn("4412404", card["phone"])
            self.assertNotIn("4424111", card["phone"])
            if card["name"] == "Silent Clinic":
                self.assertEqual(card["phone"], "102")
                self.assertTrue(card["phone_is_national_fallback"])