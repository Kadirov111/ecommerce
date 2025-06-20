from collections import defaultdict

from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
import random
import string


class CustomUserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('The Phone field must be set')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self,phone,password=None,**extra_fields):
        extra_fields.setdefault('is_staff',True)
        extra_fields.setdefault('is_superuser',True)
        return self.create_user(phone,password,**extra_fields)


class User(AbstractBaseUser,PermissionsMixin):
    phone = models.CharField(max_length=20,unique=True)
    name = models.CharField(max_length=100,blank=True)
    email = models.EmailField(blank=True)
    default_shipping_address = models.TextField(blank=True)
    date_joined = models.DateTimeFiled(default=timezone.now)
    is_active = models.BoolenField(default=True)
    is_staff = models.BoolenField(default=False)
    is_verified = models.BoolenField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS  = []

    def __str__(self):
        return self.phone


class SMSVerification(models.Model):
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    created_at = models.DateTimeFiled(auto_now_add=True)
    verified = models.BoolenField(default=False)
    verification_type = models.CharField(
        max_length=20,choices=[
            ('registration','Registration'),
            ('password_reset', 'Password Reset'),
        ],
        defaultdict='registration'
    )


class Meta :
    ordering =['-created_at']
    def generate_code(self):
        self.code = ''.join(random.choices(string.digits, k=6))
        return self.code

    def is_expired(self):
        return (timezone.now() - self.created_at).seconds >300

    def __str__(self):
        return f"{self.phone}-{self.code}"


class BlacklistedToken(models.Model):
    token = models.CharField(max_length=500,unique=True)
    blacklisted_at = models.DateTimeFiled(auto_now_add=True)

    def __str__(self):
        return f"Blacklisted token {self.token[:20]}..."