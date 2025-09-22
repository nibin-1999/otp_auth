from datetime import timedelta
import secrets

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.utils import timezone
from django.shortcuts import get_object_or_404

from .models import User, OTPCode
from .serializers import PhoneNumberSerializer
from .utils import send_otp_sms


# ----------------------------------------------------------------------
# Helper: generate a cryptographically secure OTP
# ----------------------------------------------------------------------
def generate_otp(length: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


# ----------------------------------------------------------------------
# Request OTP
# ----------------------------------------------------------------------
@api_view(["POST"])
def request_otp(request):
    """
    Accepts {"phone_number": "+911234567890"}
    Generates OTP and stores it in OTPCode table (user not created yet).
    """
    serializer = PhoneNumberSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    phone_number = serializer.validated_data["phone_number"]

    # Generate OTP
    otp = generate_otp()
    otp_record = OTPCode.objects.create(
        user=None,  # User will be created after verification
        code=otp,
        expires_at=timezone.now() + timedelta(minutes=5),
        type="signup"
    )
    # Optional: you can add a phone_number field in OTPCode if needed
    otp_record.phone_number = phone_number
    otp_record.save()

    try:
        send_otp_sms(phone_number, otp)
    except Exception as exc:
        return Response(
            {"error": f"Failed to send OTP: {exc}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    return Response({"message": "OTP sent successfully."}, status=status.HTTP_200_OK)


# ----------------------------------------------------------------------
# Verify OTP
# ----------------------------------------------------------------------
@api_view(["POST"])
def verify_otp(request):
    """
    Accepts {"phone_number": "+911234567890", "otp": "123456"}
    Verifies the OTP and creates the user if not exists.
    """
    phone_number = request.data.get("phone_number")
    otp = request.data.get("otp")

    if not phone_number or not otp:
        return Response(
            {"error": "Phone number and OTP are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Get latest OTP for this phone number
    otp_record = OTPCode.objects.filter(
        user__isnull=True,
        type="signup",
        code=otp
    ).order_by("-created_at").first()

    if not otp_record:
        return Response({"error": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

    if timezone.now() > otp_record.expires_at:
        return Response({"error": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

    # Create user after OTP verification
    user = User.objects.create(
        phone=phone_number,
        username=phone_number,  # Or generate a unique username
    )

    # Link OTP to user (optional)
    otp_record.user = user
    otp_record.is_used = True
    otp_record.save()

    # Generate auth token
    token, _ = Token.objects.get_or_create(user=user)

    return Response(
        {"message": "OTP verified successfully.", "token": token.key},
        status=status.HTTP_200_OK,
    )
