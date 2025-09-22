from rest_framework import serializers


class PhoneNumberSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=20)

    def validate_phone_number(self, value):
        if not value.startswith("+"):
            raise serializers.ValidationError(
                "Phone number must include country code, e.g., +91XXXXXXXXXX")
        return value
