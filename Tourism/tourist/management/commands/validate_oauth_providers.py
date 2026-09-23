"""OAuth provider configuration smoke test.

Validates that SUPPLIED credentials are actually accepted by each provider —
without fabricating anything and without printing secrets:

  * posts a deliberately invalid authorization code to the provider's real
    token endpoint with the configured client id/secret;
  * a provider that recognises the client answers invalid_grant (Google) or
    bad_verification_code (GitHub) => CONFIG OK;
  * anything else => CONFIG INVALID (exit 1);
  * unconfigured providers are reported as honest SKIPs (sign-in buttons
    stay disabled until credentials are supplied).

Usage: python manage.py validate_oauth_providers
"""
import json

import requests
from django.conf import settings
from django.core.management.base import BaseCommand

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"


class Command(BaseCommand):
    help = "Smoke-test Google/GitHub OAuth credentials against the real token endpoints."

    def handle(self, *args, **options):
        results = {}
        failed = False

        if getattr(settings, "GOOGLE_CLIENT_ID", "") and getattr(settings, "GOOGLE_CLIENT_SECRET", ""):
            try:
                resp = requests.post(GOOGLE_TOKEN_URL, data={
                    "code": "deliberately-invalid-code",
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": "http://localhost/auth/callback/google",
                    "grant_type": "authorization_code",
                }, timeout=15)
                body = resp.json() if resp.headers.get("content-type", "").startswith("application/json") else {}
                err = body.get("error", "")
                ok = err == "invalid_grant"  # client recognised, code rejected = expected
                results["google"] = {"configured": True, "accepted": ok,
                                     "detail": err or f"HTTP {resp.status_code}"}
            except requests.RequestException as exc:
                results["google"] = {"configured": True, "accepted": False,
                                     "detail": f"unreachable: {str(exc)[:120]}"}
        else:
            results["google"] = {"configured": False, "accepted": None,
                                 "detail": "credentials not set — social button stays disabled"}

        if getattr(settings, "GITHUB_CLIENT_ID", "") and getattr(settings, "GITHUB_CLIENT_SECRET", ""):
            try:
                resp = requests.post(GITHUB_TOKEN_URL, data={
                    "code": "deliberately-invalid-code",
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                }, headers={"Accept": "application/json"}, timeout=15)
                try:
                    body = resp.json()
                except ValueError:
                    body = {}
                err = str(body.get("error", ""))
                ok = err == "bad_verification_code"
                results["github"] = {"configured": True, "accepted": ok,
                                     "detail": err or f"HTTP {resp.status_code}"}
            except requests.RequestException as exc:
                results["github"] = {"configured": True, "accepted": False,
                                     "detail": f"unreachable: {str(exc)[:120]}"}
        else:
            results["github"] = {"configured": False, "accepted": None,
                                 "detail": "credentials not set — social button stays disabled"}

        for name, r in results.items():
            if not r["configured"]:
                self.stdout.write(self.style.WARNING(f"  SKIP  {name}: {r['detail']}"))
            elif r["accepted"]:
                self.stdout.write(self.style.SUCCESS(f"  OK    {name}: credentials accepted by provider ({r['detail']})"))
            else:
                self.stdout.write(self.style.ERROR(f"  FAIL  {name}: provider rejected configuration ({r['detail']})"))
                failed = True

        self.stdout.write(json.dumps(results, indent=2))
        if failed:
            raise SystemExit(1)
