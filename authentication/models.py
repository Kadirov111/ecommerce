import random
import string
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.db import models
from django.utils import timezone
from datetime import timedelta
from django.conf import settings


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('Phone number is required')

        user = self.model(phone=phone, **extra_fields)
        if password:
            user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed."
    )

    phone = models.CharField(
        validators=[phone_regex],
        max_length=17,
        unique=True,
        help_text="Phone number in international format"
    )
    name = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True, null=True)
    default_shipping_address = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)

    date_joined = models.DateTimeField(default=timezone.now)
    last_login = models.DateTimeField(blank=True, null=True)

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    class Meta:
        db_table = 'auth_user'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return self.phone

    @property
    def full_name(self):
        return self.name or self.phone


class OTPVerification(models.Model):
    OTP_TYPES = (
        ('registration', 'Registration'),
        ('login', 'Login'),
        ('password_reset', 'Password Reset'),
    )

    phone = models.CharField(max_length=17)
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.PositiveIntegerField(default=0)

    user_data = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'otp_verification'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone', 'otp_type']),
            models.Index(fields=['otp_code']),
        ]

    def __str__(self):
        return f"{self.phone} - {self.otp_type} - {self.otp_code}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            expiry_minutes = getattr(settings, 'OTP_CONFIG', {}).get('EXPIRY_MINUTES', 5)
            self.expires_at = timezone.now() + timedelta(minutes=expiry_minutes)
        super().save(*args, **kwargs)

    @classmethod
    def generate_otp(cls):
        """Generate a random OTP code"""
        length = getattr(settings, 'OTP_CONFIG', {}).get('LENGTH', 6)
        return ''.join(random.choices(string.digits, k=length))

    def is_expired(self):
        """Check if OTP is expired"""
        return timezone.now() > self.expires_at

    def can_attempt(self):
        max_attempts = getattr(settings, 'OTP_CONFIG', {}).get('MAX_ATTEMPTS', 3)
        return self.attempts < max_attempts

    def increment_attempts(self):
        self.attempts += 1
        self.save(update_fields=['attempts'])

    def mark_as_used(self):
        self.is_used = True
        self.save(update_fields=['is_used'])


class RefreshTokenBlacklist(models.Model):
    token = models.TextField(unique=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blacklisted_tokens')
    blacklisted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'refresh_token_blacklist'
        ordering = ['-blacklisted_at']

    def __str__(self):
        return f"Blacklisted token for {self.user.phone}"


class UserLoginAttempt(models.Model):
    phone = models.CharField(max_length=17)
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)

    success = models.BooleanField(default=False)
    attempt_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_login_attempt'
        ordering = ['-attempt_time']
        indexes = [
            models.Index(fields=['phone', 'attempt_time']),
            models.Index(fields=['ip_address', 'attempt_time']),
        ]

    def __str__(self):
        status = "Success" if self.success else "Failed"
        return f"{self.phone} - {status} - {self.attempt_time}"