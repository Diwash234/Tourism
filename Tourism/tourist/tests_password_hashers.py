"""Password hasher migration safety.

Switching the primary hasher to bcrypt must not lock anybody out: every
password already stored as ``pbkdf2_sha256$`` (or the older variants) has to
keep verifying, and new passwords must be stored with the new primary.
"""
from django.contrib.auth.hashers import (
    PBKDF2PasswordHasher,
    PBKDF2SHA1PasswordHasher,
    check_password,
    identify_hasher,
    make_password,
)
from django.test import TestCase

from .models import User


class PasswordHasherMigrationTests(TestCase):
    def test_new_passwords_use_the_bcrypt_primary(self):
        encoded = make_password("Str0ng!Pass123")
        self.assertTrue(encoded.startswith("bcrypt_sha256$"), encoded)
        self.assertTrue(check_password("Str0ng!Pass123", encoded))
        self.assertFalse(check_password("wrong", encoded))

    def test_legacy_pbkdf2_hashes_still_verify(self):
        for hasher in (PBKDF2PasswordHasher(), PBKDF2SHA1PasswordHasher()):
            with self.subTest(algorithm=hasher.algorithm):
                legacy = hasher.encode("Legacy!Pass123", hasher.salt())
                self.assertTrue(legacy.startswith(hasher.algorithm))
                # The fallback chain must still accept the old hash.
                self.assertTrue(
                    check_password("Legacy!Pass123", legacy),
                    f"{hasher.algorithm} hashes must keep verifying after the switch",
                )
                self.assertEqual(identify_hasher(legacy).algorithm, hasher.algorithm)

    def test_an_existing_user_with_a_legacy_hash_can_still_log_in(self):
        legacy_hasher = PBKDF2PasswordHasher()
        user = User.objects.create_user(
            email="legacy-hasher@test.local",
            password="Str0ng!Pass123",
        )
        # Force the stored hash to the legacy algorithm.
        user.password = legacy_hasher.encode("Str0ng!Pass123", legacy_hasher.salt())
        user.save(update_fields=["password"])
        self.assertTrue(user.password.startswith("pbkdf2"))

        self.assertTrue(User.objects.filter(email="legacy-hasher@test.local").exists())
        from django.contrib.auth import authenticate

        self.assertIsNotNone(
            authenticate(username="legacy-hasher@test.local", password="Str0ng!Pass123"),
            "a user whose hash predates the hasher switch must still authenticate",
        )

    def test_long_passwords_are_not_truncated_by_bcrypt(self):
        # bcrypt silently truncates at 72 bytes; Django's BCryptSHA256PasswordHasher
        # pre-hashes with SHA-256 specifically to avoid that.
        long_password = "correct-horse-battery-staple-" * 6  # > 72 bytes
        self.assertGreater(len(long_password.encode()), 72)
        encoded = make_password(long_password)
        self.assertTrue(check_password(long_password, encoded))
        self.assertFalse(check_password(long_password[:-1] + "X", encoded))

    def test_work_factor_is_documented_and_above_the_owasp_floor(self):
        from Tourism.hashers import PrimaryBCryptSHA256PasswordHasher

        self.assertGreaterEqual(
            PrimaryBCryptSHA256PasswordHasher.rounds,
            10,
            "bcrypt work factor must stay at or above the OWASP-recommended minimum of 10",
        )

    def test_hasher_chain_keeps_legacy_fallbacks(self):
        from django.conf import settings

        configured = list(settings.PASSWORD_HASHERS)
        self.assertEqual(
            configured[0], "Tourism.hashers.PrimaryBCryptSHA256PasswordHasher"
        )
        self.assertIn(
            "django.contrib.auth.hashers.PBKDF2PasswordHasher",
            configured,
            "PBKDF2 must remain in the chain so existing hashes keep verifying",
        )
