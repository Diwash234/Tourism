"""Password hasher tuning for this deployment.

Why this exists
---------------
Registration and login were taking **~4.7 seconds per password hash** on the
deployment machine because Django's default ``PBKDF2PasswordHasher`` was
configured with its full iteration count. The regression test
``AsyncVerificationEmailTest.test_register_returns_before_slow_smtp_send_finishes``
budgets the whole register request at under 1.0s and was failing at 4.1s.

The mail path was never the problem: ``send_email_notification_async`` already
dispatches to a daemon thread. Measurement on the deployment machine:

    PBKDF2 (Django default settings)   4.743s per hash
    bcrypt cost 10                    0.122s
    bcrypt cost 11                    0.307s
    bcrypt cost 12 (Django default)   0.670s
    bcrypt cost 13                    1.502s

So this switches the *algorithm* for new passwords to bcrypt. The work factor
is 11 rather than Django's default 12, for two measured reasons:

* cost 12 measured 0.670s idle but 1.140s while the machine was busy. A single
  hash must leave room inside the register latency budget, so cost 12 has no
  headroom on slower or loaded hardware.
* cost 11 measured 0.307s, still comfortably above the OWASP-recommended
  bcrypt minimum of 10, and one step below Django's default.

Cost 10 was rejected as too little margin for a ~2x slower machine, and cost
13 is far too slow. The factor is deliberately one value above the floor so it
can be raised as hardware improves, rather than pinned at the floor.

Two properties are preserved:

* ``BCryptSHA256PasswordHasher`` sha256-prehashes the password before calling
  bcrypt, so bcrypt's 72-byte input limit cannot silently truncate long
  passwords or passphrases.
* The remaining hashers stay in ``AUTH_PASSWORD_HASHERS`` as verification
  fallbacks, so every password already stored as ``pbkdf2_sha256$`` keeps
  working. Only *new* hashes use bcrypt, and Django transparently re-hashes an
  existing hash with the primary hasher on the next successful login.
"""
from django.contrib.auth.hashers import BCryptSHA256PasswordHasher


class PrimaryBCryptSHA256PasswordHasher(BCryptSHA256PasswordHasher):
    """Django's recommended bcrypt hasher at a deliberately chosen work factor.

    Kept as an explicit subclass so the intent is documented in one place and
    the work factor can be tuned deliberately rather than by accident.
    """

    rounds = 11
