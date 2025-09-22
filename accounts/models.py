from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from datetime import timedelta
import secrets


# -----------------------------
# User Manager
# -----------------------------
class UserManager(BaseUserManager):
    def create_user(self, phone, username=None, full_name=None, email=None, password=None, **extra_fields):
        if not phone:
            raise ValueError("Users must have a phone number")

        # Auto-generate unique username if not provided
        if not username:
            username = f"user_{secrets.token_hex(4)}"

        user = self.model(
            phone=phone,
            username=username,
            full_name=full_name,
            email=self.normalize_email(email),
            **extra_fields
        )

        # Password optional for OTP-only login
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save(using=self._db)
        return user

    def create_superuser(self, phone, username=None, full_name=None, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(phone, username, full_name, email, password, **extra_fields)


# -----------------------------
# User Model
# -----------------------------
class User(AbstractBaseUser, PermissionsMixin):
    username = models.CharField(max_length=150, unique=True)
    full_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(unique=True, null=True, blank=True)
    phone = models.CharField(max_length=20, unique=True)
    country_code = models.CharField(max_length=5, blank=True)
    role = models.CharField(max_length=50, blank=True)
    loyalty_points = models.PositiveIntegerField(default=0)

    # OTP fields
    otp = models.CharField(max_length=6, blank=True, null=True)
    otp_expires_at = models.DateTimeField(blank=True, null=True)

    # Django auth fields
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    objects = UserManager()

    USERNAME_FIELD = "phone"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.phone

    def otp_is_valid(self):
        """Check if current OTP is valid."""
        return self.otp and self.otp_expires_at and timezone.now() < self.otp_expires_at


# -----------------------------
# OTP Codes (Optional for history/log)
# -----------------------------
class OTPCode(models.Model):
    OTP_TYPE_CHOICES = [
        ("login", "Login"),
        ("signup", "Signup"),
        ("password_reset", "Password Reset"),
    ]

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="otp_codes")
    code = models.CharField(max_length=6)
    type = models.CharField(
        max_length=30, choices=OTP_TYPE_CHOICES, default="login")
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=["user", "code"]),
        ]
        ordering = ["-created_at"]

    def is_valid(self):
        return not self.is_used and timezone.now() < self.expires_at

    @classmethod
    def create_otp(cls, user, otp_code=None, otp_type="login", expiry_minutes=5):
        """Create OTP and save it to DB."""
        if not otp_code:
            otp_code = "".join(secrets.choice("0123456789") for _ in range(6))
        return cls.objects.create(
            user=user,
            code=otp_code,
            type=otp_type,
            expires_at=timezone.now() + timedelta(minutes=expiry_minutes),
        )

    def __str__(self):
        return f"{self.code} for {self.user.phone}"
