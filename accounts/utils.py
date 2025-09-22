import secrets
from twilio.rest import Client
from django.conf import settings
from twilio.base.exceptions import TwilioRestException


def generate_otp(length: int = 6) -> str:
    return "".join(secrets.choice("0123456789") for _ in range(length))


def send_otp_sms(phone_number: str, otp: str) -> str:
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    try:
        message = client.messages.create(
            body=f"Your OTP is: {otp}",
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone_number,
        )
        return message.sid
    except TwilioRestException as e:
        print(f"Failed to send OTP to {phone_number}: {e}")
        raise
