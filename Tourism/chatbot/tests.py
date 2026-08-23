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