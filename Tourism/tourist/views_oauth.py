"""
Custom, lightweight OAuth implementation -- deliberately NOT using
django-allauth or social-auth-app-django, since this project already has
a clean, simple JWT-based auth flow (rest_framework_simplejwt) and pulling
in a full third-party auth framework would mean maintaining two parallel
auth systems. This does the token exchange directly with each provider's
API and issues the exact same JWT pair RegisterView/LoginView already do.

Frontend flow this expects:
1. Frontend redirects the user to Google's/GitHub's OAuth consent screen
   directly (standard OAuth authorize URL, built client-side or via a
   small helper endpoint -- not shown here, this is the callback half).
2. Provider redirects back to the frontend with a `code` query param.
3. Frontend POSTs that code to /auth/google/callback/ or
   /auth/github/callback/ (this file).
4. This exchanges the code for the provider's access token, fetches the
   user's email/profile, creates-or-links a User, and returns the same
   {access, refresh} JWT pair as the existing LoginView.
"""
import logging

import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

logger = logging.getLogger(__name__)
User = get_user_model()


def _issue_jwt_pair(user):
    """Same shape LoginView already returns -- frontend handles both identically."""
    refresh = RefreshToken.for_user(user)
    return {"access": str(refresh.access_token), "refresh": str(refresh)}


def _get_or_link_user(email, provider, provider_uid, first_name="", last_name=""):
    """
    Links to an existing account with the same email (regardless of how
    it was originally created) rather than creating a duplicate, and
    records which provider/uid this login came from.
    """
    with transaction.atomic():
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "auth_provider": provider,
                "provider_uid": provider_uid,
                "is_verified": True,  # provider already verified this email
            },
        )
        if not created and not user.provider_uid:
            # Existing email/password account logging in via OAuth for the
            # first time -- link it rather than leaving it unlinked.
            user.auth_provider = provider
            user.provider_uid = provider_uid
            user.is_verified = True
            user.save(update_fields=["auth_provider", "provider_uid", "is_verified"])
    return user


class GoogleOAuthCallbackView(APIView):
    """
    POST /auth/google/callback/  {"code": "...", "redirect_uri": "..."}
    `redirect_uri` must exactly match what was used to obtain `code` on
    the frontend (Google validates this) -- passed through rather than
    hardcoded so dev/staging/prod can each use their own callback URL.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get("code")
        redirect_uri = request.data.get("redirect_uri")
        if not code or not redirect_uri:
            return Response({"detail": "code and redirect_uri are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_response = requests.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "code": code,
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uri": redirect_uri,
                    "grant_type": "authorization_code",
                },
                timeout=10,
            )
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]

            profile_response = requests.get(
                "https://www.googleapis.com/oauth2/v3/userinfo",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            profile_response.raise_for_status()
            profile = profile_response.json()
        except (requests.RequestException, KeyError) as exc:
            logger.warning("Google OAuth exchange failed: %s", exc)
            return Response({"detail": "Google authentication failed."}, status=status.HTTP_400_BAD_REQUEST)

        email = profile.get("email")
        if not email:
            return Response({"detail": "Google account has no email."}, status=status.HTTP_400_BAD_REQUEST)

        user = _get_or_link_user(
            email=email,
            provider=User.AuthProvider.GOOGLE,
            provider_uid=profile.get("sub", ""),
            first_name=profile.get("given_name", ""),
            last_name=profile.get("family_name", ""),
        )
        return Response({**_issue_jwt_pair(user), "user": {"id": user.id, "email": user.email, "name": user.first_name}})


class GithubOAuthCallbackView(APIView):
    """
    POST /auth/github/callback/  {"code": "..."}
    GitHub's token exchange doesn't require redirect_uri to be resent
    (unlike Google) as long as it matches what's registered on the OAuth
    App itself.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        code = request.data.get("code")
        if not code:
            return Response({"detail": "code is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            token_response = requests.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "code": code,
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                },
                headers={"Accept": "application/json"},
                timeout=10,
            )
            token_response.raise_for_status()
            access_token = token_response.json()["access_token"]

            profile_response = requests.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {access_token}"},
                timeout=10,
            )
            profile_response.raise_for_status()
            profile = profile_response.json()

            email = profile.get("email")
            if not email:
                # GitHub only returns a public email if the user set one;
                # the dedicated emails endpoint is needed otherwise.
                emails_response = requests.get(
                    "https://api.github.com/user/emails",
                    headers={"Authorization": f"Bearer {access_token}"},
                    timeout=10,
                )
                emails_response.raise_for_status()
                primary = next((e for e in emails_response.json() if e.get("primary")), None)
                email = primary["email"] if primary else None
        except (requests.RequestException, KeyError) as exc:
            logger.warning("GitHub OAuth exchange failed: %s", exc)
            return Response({"detail": "GitHub authentication failed."}, status=status.HTTP_400_BAD_REQUEST)

        if not email:
            return Response(
                {"detail": "GitHub account has no accessible email. Make an email public or use another login method."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        name_parts = (profile.get("name") or "").split(" ", 1)
        user = _get_or_link_user(
            email=email,
            provider=User.AuthProvider.GITHUB,
            provider_uid=str(profile.get("id", "")),
            first_name=name_parts[0] if name_parts else "",
            last_name=name_parts[1] if len(name_parts) > 1 else "",
        )
        return Response({**_issue_jwt_pair(user), "user": {"id": user.id, "email": user.email, "name": user.first_name}})