"""Tests for permission-based media review and the configurable release gate.

These cover the promises the feature makes:
  * a score can only be written by an authorised reviewer, with provenance;
  * nothing invents or backfills a score;
  * the release gate is configurable and says which rule is active;
  * every image is classified so a UI (and a release) can explain itself.
"""
from __future__ import annotations

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from tourist.media_review import (
    ACTION_APPROVE_REVIEW,
    ACTION_REVIEW,
    ACTION_SCORE_AUTHENTICITY,
    ACTION_SCORE_DESTINATION_MATCH,
    GATE_APPROVAL,
    GATE_SCORED,
    MediaReviewError,
    STATE_AWAITING_REVIEW,
    STATE_BELOW_THRESHOLD,
    STATE_CANONICAL,
    STATE_ELIGIBLE,
    assign_scores,
    can_approve_review,
    can_assign_authenticity,
    can_assign_destination_match,
    can_review_media,
    image_gate_exclusion,
    image_satisfies_application_rule,
    media_review_capabilities,
    media_review_state,
)
from tourist.models import (
    Category,
    Destination,
    DestinationImage,
    StaffCapabilityProfile,
)

User = get_user_model()


class MediaReviewTestBase(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name="Review Category")
        self.destination = Destination.objects.create(
            name="Pashupatinath Temple",
            slug="pashupatinath-temple",
            category=self.category,
            district="Kathmandu",
            source="wikimedia",
            external_id=4242,
            status=Destination.SubmissionStatus.APPROVED,
            is_active=True,
            is_user_submitted=False,
            latitude=27.7104,
            longitude=85.3487,
        )
        # No passwords: these tests authenticate with force_authenticate, and
        # hashing four PBKDF2 passwords in every setUp is pure overhead.
        self.admin = User.objects.create_user(
            email="review-admin@example.com", password=None, role="admin"
        )
        self.manager = User.objects.create_user(
            email="review-manager@example.com", password=None,
            role="content_moderator",
        )
        self.member = User.objects.create_user(
            email="review-member@example.com", password=None, role="staff"
        )
        self.outsider = User.objects.create_user(
            email="review-outsider@example.com", password=None, role="tourist"
        )

    def make_image(self, **kwargs):
        defaults = {
            "destination": self.destination,
            "external_url": "https://upload.wikimedia.org/x/pashupatinath.jpg",
            "source_url": "https://commons.wikimedia.org/wiki/File:Pashupatinath.jpg",
            "source": "wikimedia",
            "caption": "Pashupatinath Temple",
            "alt_text": "Pashupatinath Temple Kathmandu",
            "verification_status": DestinationImage.ImageStatus.APPROVED,
            "is_verified": True,
        }
        defaults.update(kwargs)
        return DestinationImage.objects.create(**defaults)


class MediaReviewPermissionTests(MediaReviewTestBase):
    def test_admin_and_manager_can_review_without_explicit_grant(self):
        self.assertTrue(can_review_media(self.admin))
        self.assertTrue(can_review_media(self.manager))
        self.assertTrue(can_assign_authenticity(self.manager))
        self.assertTrue(can_assign_destination_match(self.manager))

    def test_member_cannot_review_until_granted(self):
        self.assertFalse(can_review_media(self.member))
        self.assertFalse(can_assign_authenticity(self.member))

    def test_permission_grant_enables_member_review(self):
        permission = Permission.objects.get(codename="review_destinationimage")
        self.member.user_permissions.add(permission)
        member = User.objects.get(pk=self.member.pk)  # drop the perm cache
        self.assertTrue(can_review_media(member))
        self.assertFalse(can_assign_authenticity(member))

    def test_capability_profile_delegation_records_grantor(self):
        profile = StaffCapabilityProfile.objects.create(
            user=self.member,
            capabilities={"images": [ACTION_REVIEW, ACTION_SCORE_AUTHENTICITY]},
            assigned_by=self.admin,
        )
        member = User.objects.get(pk=self.member.pk)
        self.assertTrue(can_review_media(member))
        self.assertTrue(can_assign_authenticity(member))
        self.assertFalse(can_assign_destination_match(member))
        self.assertFalse(can_approve_review(member))
        capabilities = media_review_capabilities(member)
        self.assertEqual(capabilities["capability_granted_by"], self.admin.email)
        self.assertIsNotNone(capabilities["capability_granted_at"])

    def test_deactivated_profile_revokes_capability(self):
        StaffCapabilityProfile.objects.create(
            user=self.member,
            capabilities={"images": [ACTION_REVIEW]},
            assigned_by=self.admin,
            is_active=False,
        )
        member = User.objects.get(pk=self.member.pk)
        self.assertFalse(can_review_media(member))

    def test_invalid_capability_action_is_rejected_by_the_model(self):
        from django.core.exceptions import ValidationError

        profile = StaffCapabilityProfile(user=self.member, capabilities={"images": ["invent_score"]})
        with self.assertRaises(ValidationError):
            profile.clean()

    def test_approve_review_action_is_separately_grantable(self):
        StaffCapabilityProfile.objects.create(
            user=self.member,
            capabilities={"images": [ACTION_REVIEW, ACTION_APPROVE_REVIEW]},
            assigned_by=self.admin,
        )
        member = User.objects.get(pk=self.member.pk)
        self.assertTrue(can_approve_review(member))
        self.assertFalse(can_assign_authenticity(member))


class MediaReviewScoreTests(MediaReviewTestBase):
    def test_assigning_scores_records_provenance(self):
        image = self.make_image()
        changes = assign_scores(
            image,
            reviewer=self.manager,
            authenticity=0.91,
            destination_match=0.88,
        )
        image.refresh_from_db()
        self.assertEqual(len(changes), 2)
        self.assertEqual(image.authenticity_score, 0.91)
        self.assertEqual(image.authenticity_score_by, self.manager)
        self.assertIsNotNone(image.authenticity_score_at)
        self.assertEqual(image.destination_match_score_by, self.manager)
        self.assertEqual(image.media_reviewed_by, self.manager)

    def test_unauthorised_user_cannot_assign(self):
        image = self.make_image()
        with self.assertRaises(MediaReviewError):
            assign_scores(image, reviewer=self.outsider, authenticity=0.99)

    def test_missing_score_is_never_invented(self):
        image = self.make_image()
        with self.assertRaises(MediaReviewError):
            assign_scores(image, reviewer=self.manager, authenticity=None)
        image.refresh_from_db()
        self.assertIsNone(image.authenticity_score)

    def test_empty_payload_changes_nothing(self):
        image = self.make_image()
        with self.assertRaises(MediaReviewError):
            assign_scores(image, reviewer=self.manager)
        image.refresh_from_db()
        self.assertIsNone(image.authenticity_score)
        self.assertIsNone(image.authenticity_score_by)

    def test_out_of_range_score_is_rejected(self):
        image = self.make_image()
        with self.assertRaises(MediaReviewError):
            assign_scores(image, reviewer=self.manager, authenticity=1.5)
        with self.assertRaises(MediaReviewError):
            assign_scores(image, reviewer=self.manager, destination_match=-0.2)

    def test_boolean_score_is_rejected(self):
        image = self.make_image()
        with self.assertRaises(MediaReviewError):
            assign_scores(image, reviewer=self.manager, authenticity=True)

    def test_member_without_score_permission_cannot_score(self):
        StaffCapabilityProfile.objects.create(
            user=self.member,
            capabilities={"images": [ACTION_REVIEW]},
            assigned_by=self.admin,
        )
        member = User.objects.get(pk=self.member.pk)
        image = self.make_image()
        with self.assertRaises(MediaReviewError):
            assign_scores(image, reviewer=member, authenticity=0.9)

    def test_score_assignment_is_audited(self):
        from audit.models import AuditLog

        image = self.make_image()
        assign_scores(image, reviewer=self.manager, authenticity=0.9)
        self.assertTrue(
            AuditLog.objects.filter(action="media.score.assigned").exists()
        )

    def test_approve_requires_application_rule(self):
        image = self.make_image(verification_status=DestinationImage.ImageStatus.PENDING, is_verified=False)
        with self.assertRaises(MediaReviewError):
            assign_scores(image, reviewer=self.admin, approve=True)


class MediaReviewStateTests(MediaReviewTestBase):
    def test_unreviewed_image_awaits_review_under_scored_gate(self):
        image = self.make_image()
        # The site already displays it (app rule passes) but the scored gate is
        # holding it back, so the actionable state is "eligible", not "awaiting".
        self.assertEqual(media_review_state(image), STATE_ELIGIBLE)
        self.assertEqual(image_gate_exclusion(image), "awaiting_media_review")

    def test_fabricated_legacy_score_counts_as_unreviewed(self):
        """A score with no named reviewer must not pass the gate."""
        image = self.make_image(authenticity_score=0.9, destination_match_score=0.9)
        self.assertEqual(image_gate_exclusion(image), "authenticity_score_unreviewed")
        self.assertEqual(media_review_state(image), STATE_ELIGIBLE)

    def test_reviewed_scores_pass_the_scored_gate(self):
        image = self.make_image()
        assign_scores(
            image, reviewer=self.manager, authenticity=0.93, destination_match=0.91
        )
        image.refresh_from_db()
        self.assertIsNone(image_gate_exclusion(image))
        self.assertEqual(media_review_state(image), STATE_CANONICAL)

    def test_below_threshold_is_reported_distinctly(self):
        image = self.make_image()
        assign_scores(
            image, reviewer=self.manager, authenticity=0.40, destination_match=0.95
        )
        image.refresh_from_db()
        self.assertEqual(
            image_gate_exclusion(image), "authenticity_score_below_threshold"
        )
        self.assertEqual(media_review_state(image), STATE_BELOW_THRESHOLD)

    def test_approval_gate_accepts_unreviewed_scores_but_records_the_state(self):
        image = self.make_image()
        with override_settings(PUBLIC_SNAPSHOT_MEDIA_GATE=GATE_APPROVAL):
            self.assertIsNone(image_gate_exclusion(image))
            self.assertEqual(media_review_state(image), STATE_CANONICAL)

    def test_approval_gate_still_rejects_non_specific_images(self):
        """A photo whose URL names a different known place is not this place's."""
        image = self.make_image(
            external_url="https://upload.wikimedia.org/wikipedia/commons/9/99/Phewa_Lake_Pokhara.jpg",
            source_url="https://commons.wikimedia.org/wiki/File:Phewa_Lake_Pokhara.jpg",
        )
        with override_settings(PUBLIC_SNAPSHOT_MEDIA_GATE=GATE_APPROVAL):
            self.assertEqual(
                image_gate_exclusion(image), "not_destination_specific"
            )

    def test_approval_gate_still_requires_verified_approved(self):
        image = self.make_image(is_verified=False)
        with override_settings(PUBLIC_SNAPSHOT_MEDIA_GATE=GATE_APPROVAL):
            self.assertEqual(image_gate_exclusion(image), "not_verified")

    def test_missing_attribution_blocks_the_release_but_not_the_site(self):
        """source_url is a release requirement, not part of the site's rule."""
        image = self.make_image(source_url="")
        with override_settings(PUBLIC_SNAPSHOT_MEDIA_GATE=GATE_APPROVAL):
            self.assertTrue(image_satisfies_application_rule(image))
            self.assertEqual(image_gate_exclusion(image), "missing_source_url")
            # Actionable work: the site shows it, the release needs attribution.
            self.assertEqual(media_review_state(image), STATE_ELIGIBLE)

    def test_app_eligible_but_gate_blocked_is_labelled_eligible(self):
        """The site shows it; the scored gate is what holds it back."""
        image = self.make_image()
        self.assertEqual(media_review_state(image), STATE_ELIGIBLE)

    def test_not_yet_approved_is_awaiting_review(self):
        image = self.make_image(
            verification_status=DestinationImage.ImageStatus.PENDING, is_verified=False
        )
        self.assertEqual(media_review_state(image), STATE_AWAITING_REVIEW)

    def test_all_four_states_are_reachable_and_distinct(self):
        states = set()
        # awaiting: not approved yet
        states.add(
            media_review_state(
                self.make_image(
                    verification_status=DestinationImage.ImageStatus.PENDING, is_verified=False
                )
            )
        )
        # eligible: app rule passes, scored gate blocks
        states.add(media_review_state(self.make_image()))
        # below threshold: genuinely reviewed and low
        low = self.make_image()
        assign_scores(low, reviewer=self.manager, authenticity=0.2, destination_match=0.95)
        states.add(media_review_state(low))
        # canonical: reviewed and good
        good = self.make_image()
        assign_scores(good, reviewer=self.manager, authenticity=0.95, destination_match=0.95)
        states.add(media_review_state(good))
        self.assertEqual(
            states,
            {STATE_AWAITING_REVIEW, STATE_ELIGIBLE, STATE_BELOW_THRESHOLD, STATE_CANONICAL},
        )

    def test_default_gate_is_scored(self):
        self.assertEqual(media_review_capabilities(self.admin)["active_gate"], GATE_SCORED)
    def test_invalid_gate_is_rejected(self):
        from tourist.media_review import resolve_media_gate

        with override_settings(PUBLIC_SNAPSHOT_MEDIA_GATE="whatever"):
            with self.assertRaises(ValueError):
                resolve_media_gate()


class MediaReviewApiTests(MediaReviewTestBase, APITestCase):
    def _login(self, user):
        self.client.force_authenticate(user=user)

    def test_capabilities_endpoint_reports_the_seven_answers(self):
        self._login(self.member)
        response = self.client.get("/api/v1/admin/media-review/capabilities")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        for key in (
            "can_review_media",
            "can_assign_authenticity",
            "can_assign_destination_match",
            "can_approve_review",
            "capability_granted_by",
            "capability_granted_at",
            "active_gate",
        ):
            self.assertIn(key, payload)
        self.assertFalse(payload["can_review_media"])

    def test_queue_is_scoped_and_explains_reasons(self):
        self.make_image()
        self._login(self.admin)
        response = self.client.get("/api/v1/admin/media-review/queue")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("active_gate", payload)
        self.assertIn("state_summary", payload)
        self.assertTrue(payload["results"])
        self.assertTrue(all("review_state" in row for row in payload["results"]))

    def test_score_endpoint_rejects_an_empty_submission(self):
        image = self.make_image()
        self._login(self.admin)
        response = self.client.post(
            f"/api/v1/admin/media-review/{image.pk}/score", {}, format="json"
        )
        self.assertEqual(response.status_code, 400)
        image.refresh_from_db()
        self.assertIsNone(image.authenticity_score)

    def test_score_endpoint_records_a_real_review(self):
        image = self.make_image()
        self._login(self.manager)
        response = self.client.post(
            f"/api/v1/admin/media-review/{image.pk}/score",
            {"authenticity_score": 0.94, "destination_match_score": 0.9},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        image.refresh_from_db()
        self.assertEqual(image.authenticity_score, 0.94)
        self.assertEqual(image.authenticity_score_by, self.manager)
        self.assertEqual(
            response.json()["provenance"]["authenticity_score"]["assigned_by"],
            self.manager.email,
        )

    def test_partial_permission_returns_403_and_writes_nothing(self):
        """A reviewer who may review but not score destination-match gets 403.

        This is the path where a mixed submission could half-apply, so it also
        asserts that no score is written at all.
        """
        StaffCapabilityProfile.objects.create(
            user=self.member,
            capabilities={"images": [ACTION_REVIEW, ACTION_SCORE_AUTHENTICITY]},
            assigned_by=self.admin,
        )
        member = User.objects.get(pk=self.member.pk)
        image = self.make_image()
        self._login(member)
        response = self.client.post(
            f"/api/v1/admin/media-review/{image.pk}/score",
            {"authenticity_score": 0.93, "destination_match_score": 0.99},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
        self.assertIn("destination-match", response.json()["detail"])
        image.refresh_from_db()
        # Neither score may be written when one of them is refused.
        self.assertIsNone(image.authenticity_score)
        self.assertIsNone(image.authenticity_score_by_id)
        self.assertIsNone(image.destination_match_score)

    def test_delegated_reviewer_can_read_the_queue_and_detail(self):
        """A reviewer who cannot score everything must still be able to work."""
        StaffCapabilityProfile.objects.create(
            user=self.member,
            capabilities={"images": [ACTION_REVIEW, ACTION_SCORE_AUTHENTICITY]},
            assigned_by=self.admin,
        )
        member = User.objects.get(pk=self.member.pk)
        image = self.make_image()
        self._login(member)

        queue = self.client.get("/api/v1/admin/media-review/queue")
        self.assertEqual(queue.status_code, 200)
        self.assertIn(image.pk, [row["id"] for row in queue.json()["results"]])

        detail = self.client.get(f"/api/v1/admin/media-review/{image.pk}")
        self.assertEqual(detail.status_code, 200)
        self.assertEqual(detail.json()["id"], image.pk)
        self.assertIn("provenance", detail.json())

    def test_score_endpoint_forbids_an_unauthorised_user(self):
        image = self.make_image()
        self._login(self.outsider)
        response = self.client.post(
            f"/api/v1/admin/media-review/{image.pk}/score",
            {"authenticity_score": 0.99},
            format="json",
        )
        self.assertIn(response.status_code, (401, 403))
        image.refresh_from_db()
        self.assertIsNone(image.authenticity_score)

    def test_delegation_grants_a_member_and_records_the_grantor(self):
        self._login(self.admin)
        response = self.client.post(
            "/api/v1/admin/media-review/delegation",
            {
                "email": self.member.email,
                "actions": [ACTION_REVIEW, ACTION_SCORE_AUTHENTICITY],
                "grant": "true",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        member = User.objects.get(pk=self.member.pk)
        self.assertTrue(can_review_media(member))
        self.assertTrue(can_assign_authenticity(member))
        self.assertEqual(
            response.json()["capabilities"]["capability_granted_by"], self.admin.email
        )

    def test_delegation_is_refused_for_a_non_delegating_user(self):
        StaffCapabilityProfile.objects.create(
            user=self.member,
            capabilities={"images": [ACTION_REVIEW]},
            assigned_by=self.admin,
        )
        member = User.objects.get(pk=self.member.pk)
        self._login(member)
        response = self.client.post(
            "/api/v1/admin/media-review/delegation",
            {"email": self.outsider.email, "grant": "true"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    def test_delegation_rejects_unknown_actions(self):
        self._login(self.admin)
        response = self.client.post(
            "/api/v1/admin/media-review/delegation",
            {"email": self.member.email, "actions": ["invent_anything"]},
            format="json",
        )
        self.assertEqual(response.status_code, 400)
