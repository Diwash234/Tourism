from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerificationToken, PasswordResetToken, SMSVerificationToken
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
    UpdateLocationSerializer,
)
from .utils import send_email_notification_async, resolve_location, issue_phone_verification

User = get_user_model()

TOKEN_LIFETIME_HOURS = 24


def _issue_email_verification(user):
    token = EmailVerificationToken.objects.create(
        user=user, expires_at=timezone.now() + timedelta(hours=TOKEN_LIFETIME_HOURS)
    )
    from django.conf import settings

    link = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
    send_email_notification_async(
        user.email,
        "Verify your email - Tourism Portal",
        f"Hi {user.first_name or user.email},\n\nPlease verify your email by visiting:\n{link}\n\n"
        f"This link expires in {TOKEN_LIFETIME_HOURS} hours.",
    )
    return token


class RegisterView(generics.CreateAPIView):
    """Register a new tourist account and send an email verification link."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        _issue_email_verification(user)
        if user.phone_number:
            issue_phone_verification(user)
        return Response(
            {
                "message": "Registration successful. Please check your email to verify your account.",
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """
    Email + password login with HONEST, specific failure reasons.

    SimpleJWT's stock view lumps "unknown email", "wrong password" and
    "deactivated account" into one vague 401 ("No active account found
    with the given credentials") — which made it look like login was
    broken for correct credentials too. This view reports exactly what
    is wrong and points at the fix:

      404 email_not_found      → sign up first
      403 account_deactivated  → contact support
      401 wrong_password       → try again / forgot password
      200 (+verification_required when email unverified)
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"
    serializer_class = None

    def post(self, request):
        email = str(request.data.get("email") or "").strip()
        password = str(request.data.get("password") or "")
        if not email:
            return Response({"detail": "Email is required.", "code": "missing_email"},
                            status=status.HTTP_400_BAD_REQUEST)
        if not password:
            return Response({"detail": "Password is required.", "code": "missing_password"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {
                    "detail": f"No account found with {email}. If you don't have an account yet, sign up first.",
                    "code": "email_not_found",
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        if not user.is_active:
            return Response(
                {
                    "detail": "This account has been deactivated. Please contact support to reactivate it.",
                    "code": "account_deactivated",
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        if not user.check_password(password):
            return Response(
                {
                    "detail": "Incorrect password for this email. Please try again or use 'Forgot password'.",
                    "code": "wrong_password",
                },
                status=status.HTTP_401_UNAUTHORIZED,
            )

        refresh = RefreshToken.for_user(user)
        data = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "user": UserProfileSerializer(user).data,
        }
        if not user.is_verified:
            data["verification_required"] = True
            data["verification_hint"] = (
                "Your email is not verified yet. Use 'Resend verification email' "
                "below the login form (or check your inbox for the original link)."
            )
        return Response(data)


class ResendVerificationByEmailView(APIView):
    """
    POST /auth/resend-verification/  {"email": "..."}

    Re-sends the email verification link for an existing, UNVERIFIED
    account. No login required (the user may not be able to log in yet),
    rate-limited to one send per 60 seconds per address, and answers
    with a specific reason instead of a blank failure.
    """

    permission_classes = [permissions.AllowAny]
    throttle_scope = "auth"
    serializer_class = None

    def post(self, request):
        from django.core.cache import cache

        email = str(request.data.get("email") or "").strip()
        if not email:
            return Response({"detail": "Email is required.", "code": "missing_email"},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response(
                {"detail": f"No account found with {email}.", "code": "email_not_found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if user.is_verified:
            return Response({"detail": "Email already verified."},
                            status=status.HTTP_400_BAD_REQUEST)

        key = f"resend-verify:{email.lower()}"
        if cache.get(key):
            return Response(
                {
                    "detail": "A verification email was sent recently — please wait a minute, "
                              "then check your inbox (and spam folder)."
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        _issue_email_verification(user)
        cache.set(key, 1, 60)
        return Response(
            {
                "message": f"Verification link sent to {email} — check your inbox (and spam folder). "
                           f"It expires in {TOKEN_LIFETIME_HOURS} hours."
            }
        )


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = VerifyEmailSerializer

    @extend_schema(request=VerifyEmailSerializer)
    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_value = serializer.validated_data["token"]

        try:
            token = EmailVerificationToken.objects.get(token=token_value)
        except EmailVerificationToken.DoesNotExist:
            return Response({"detail": "Invalid verification token."}, status=status.HTTP_400_BAD_REQUEST)

        if not token.is_valid():
            return Response({"detail": "Token expired or already used."}, status=status.HTTP_400_BAD_REQUEST)

        token.is_used = True
        token.save(update_fields=["is_used"])
        user = token.user
        user.is_verified = True
        user.save(update_fields=["is_verified"])
        return Response({"message": "Email verified successfully."})


class VerifyPhoneView(APIView):
    """
    POST /auth/verify-phone/  {"code": "123456"}
    Checks the submitted OTP against the current user's latest
    SMSVerificationToken. Requires authentication (unlike email
    verification, which uses a token in a link) since the OTP alone is
    too short-lived/guessable to double as an auth credential on its own.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        code = str(request.data.get("code", "")).strip()
        if not code:
            return Response({"detail": "code is required."}, status=status.HTTP_400_BAD_REQUEST)

        token = (
            SMSVerificationToken.objects.filter(user=request.user, is_used=False)
            .order_by("-created_at")
            .first()
        )
        if not token:
            return Response({"detail": "No pending verification code. Request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        if not token.is_valid():
            return Response({"detail": "Code expired or too many attempts. Request a new one."}, status=status.HTTP_400_BAD_REQUEST)

        if token.code != code:
            token.attempt_count += 1
            token.save(update_fields=["attempt_count"])
            return Response({"detail": "Incorrect code."}, status=status.HTTP_400_BAD_REQUEST)

        token.is_used = True
        token.save(update_fields=["is_used"])
        request.user.phone_verified = True
        request.user.save(update_fields=["phone_verified"])
        return Response({"message": "Phone number verified successfully."})


class ResendPhoneOTPView(APIView):
    """
    POST /auth/resend-phone-otp/
    Rate limited to 1 send per 60 seconds per user -- Twilio charges per
    SMS, so this is cost control as much as abuse prevention.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.phone_number:
            return Response({"detail": "No phone number on file."}, status=status.HTTP_400_BAD_REQUEST)

        recent = (
            SMSVerificationToken.objects.filter(user=request.user)
            .order_by("-created_at")
            .first()
        )
        if recent and (timezone.now() - recent.created_at).total_seconds() < 60:
            return Response(
                {"detail": "Please wait a minute before requesting another code."},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        issue_phone_verification(request.user)
        if not getattr(issue_phone_verification, "last_delivered", False):
            from django.conf import settings as djsettings
            configured = bool(djsettings.TWILIO_ACCOUNT_SID and djsettings.TWILIO_AUTH_TOKEN and djsettings.TWILIO_FROM_NUMBER)
            return Response(
                {"detail": ("SMS could not be delivered to your number right now. Check the number in your profile or try again shortly."
                            if configured else "SMS verification is not enabled on this server yet.")},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        return Response({"message": "Verification code sent."})


class ResendVerificationEmailView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    throttle_scope = "auth"
    serializer_class = None

    def post(self, request):
        if request.user.is_verified:
            return Response({"detail": "Email already verified."}, status=status.HTTP_400_BAD_REQUEST)
        _issue_email_verification(request.user)
        return Response({"message": "Verification email sent."})


class LogoutView(APIView):
    """Blacklists the supplied refresh token so it can no longer be used."""

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response({"detail": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)


class ForgotPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "password_reset"
    serializer_class = ForgotPasswordSerializer

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        # Always respond with 200 to avoid leaking which emails are registered.
        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            return Response({"message": "If that email exists, a reset link has been sent."})

        from django.conf import settings

        token = PasswordResetToken.objects.create(
            user=user, expires_at=timezone.now() + timedelta(hours=1)
        )
        link = f"{settings.FRONTEND_URL}/reset-password?token={token.token}"
        send_email_notification_async(
            user.email,
            "Reset your password - Tourism Portal",
            f"Hi {user.first_name or user.email},\n\nReset your password here:\n{link}\n\nThis link expires in 1 hour.",
        )
        return Response({"message": "If that email exists, a reset link has been sent."})


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    throttle_scope = "password_reset"
    serializer_class = ResetPasswordSerializer

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token_value = serializer.validated_data["token"]
        new_password = serializer.validated_data["new_password"]

        try:
            token = PasswordResetToken.objects.get(token=token_value)
        except PasswordResetToken.DoesNotExist:
            return Response({"detail": "Invalid reset token."}, status=status.HTTP_400_BAD_REQUEST)

        if not token.is_valid():
            return Response({"detail": "Token expired or already used."}, status=status.HTTP_400_BAD_REQUEST)

        user = token.user
        user.set_password(new_password)
        user.save(update_fields=["password"])
        token.is_used = True
        token.save(update_fields=["is_used"])
        return Response({"message": "Password reset successful. You can now log in."})


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user

        if not user.check_password(serializer.validated_data["old_password"]):
            return Response({"old_password": "Incorrect password."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        return Response({"message": "Password changed successfully."})


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UpdateLocationView(APIView):
    """
    Sets the user's current location. Prefers browser-supplied GPS
    coordinates; falls back to server-side GeoIP lookup when GPS is absent.
    Automatically reverse-geocodes GPS coordinates into real Nepal cities.
    """

    permission_classes = [permissions.IsAuthenticated]
    serializer_class = UpdateLocationSerializer

    def post(self, request):
        serializer = UpdateLocationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lat = serializer.validated_data.get("latitude")
        lon = serializer.validated_data.get("longitude")

        location = resolve_location(request, gps_latitude=lat, gps_longitude=lon)
        user = request.user
        if location.get("latitude") is not None:
            user.latitude = location["latitude"]
        if location.get("longitude") is not None:
            user.longitude = location["longitude"]
        if location.get("country"):
            user.country = location["country"]
        if location.get("city"):
            user.city = location["city"]
        user.location_source = location.get("source") or "gps"
        user.save(update_fields=["latitude", "longitude", "country", "city", "location_source"])
        return Response(UserProfileSerializer(user).data)

    put = post
    patch = post


class DetectLocationView(APIView):
    """Public endpoint: detects country/city/lat/lon purely from request IP (GeoIP)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = None

    def get(self, request):
        location = resolve_location(request)
        return Response(location)

class MyCapabilitiesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = None

    def get(self, request):
        user = request.user
        admin = user.is_superuser or user.role in {"admin", "super_admin", "tourism_admin"}
        if admin:
            from .models import StaffCapabilityProfile
            capabilities = {module: ["*"] for module in StaffCapabilityProfile.MODULES}
            districts = []
        else:
            profile = getattr(user, "capability_profile", None)
            capabilities = profile.capabilities if profile and profile.is_active else {}
            districts = profile.managed_districts if profile else []
        return Response({"role": user.role, "is_admin": admin, "capabilities": capabilities, "managed_districts": districts})
