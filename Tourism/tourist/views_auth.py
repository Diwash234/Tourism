from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import EmailVerificationToken, PasswordResetToken
from .serializers import (
    RegisterSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyEmailSerializer,
    UpdateLocationSerializer,
)
from .utils import send_email_notification, resolve_location

User = get_user_model()

TOKEN_LIFETIME_HOURS = 24


def _issue_email_verification(user):
    token = EmailVerificationToken.objects.create(
        user=user, expires_at=timezone.now() + timedelta(hours=TOKEN_LIFETIME_HOURS)
    )
    from django.conf import settings

    link = f"{settings.FRONTEND_URL}/verify-email?token={token.token}"
    send_email_notification(
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
        return Response(
            {
                "message": "Registration successful. Please check your email to verify your account.",
                "user": UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
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
        send_email_notification(
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
        user.latitude = location["latitude"]
        user.longitude = location["longitude"]
        if location.get("country"):
            user.country = location["country"]
        if location.get("city"):
            user.city = location["city"]
        user.location_source = location["source"]
        user.save(update_fields=["latitude", "longitude", "country", "city", "location_source"])
        return Response(UserProfileSerializer(user).data)


class DetectLocationView(APIView):
    """Public endpoint: detects country/city/lat/lon purely from request IP (GeoIP)."""

    permission_classes = [permissions.AllowAny]
    serializer_class = None

    def get(self, request):
        location = resolve_location(request)
        return Response(location)
