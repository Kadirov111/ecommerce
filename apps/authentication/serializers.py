from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, OTPVerification
from .utils import validate_phone_number
import re


class AuthorizeSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=17)
    password = serializers.CharField(write_only=True, required=False)

    def validate_phone(self, value):
        return validate_phone_number(value)

    def validate_password(self, value):
        if value:
            try:
                validate_password(value)
            except ValidationError as e:
                raise serializers.ValidationError(list(e.messages))
        return value


class VerifySerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=17)
    code = serializers.CharField(max_length=6, min_length=6)
    password = serializers.CharField(write_only=True, required=False)
    name = serializers.CharField(max_length=100, required=False)

    def validate_phone(self, value):
        return validate_phone_number(value)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Code must contain only digits")
        return value

    def validate_password(self, value):
        if value:
            try:
                validate_password(value)
            except ValidationError as e:
                raise serializers.ValidationError(list(e.messages))
        return value


class LoginSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=17)
    password = serializers.CharField(write_only=True)

    def validate_phone(self, value):
        return validate_phone_number(value)

    def validate(self, attrs):
        phone = attrs.get('phone')
        password = attrs.get('password')

        if phone and password:
            user = authenticate(phone=phone, password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            if not user.is_verified:
                raise serializers.ValidationError("Phone number not verified")

            attrs['user'] = user
        else:
            raise serializers.ValidationError("Phone and password are required")

        return attrs


class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


class ForgotPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=17)

    def validate_phone(self, value):
        return validate_phone_number(value)

    def validate(self, attrs):
        phone = attrs.get('phone')
        try:
            user = User.objects.get(phone=phone)
            if not user.is_active:
                raise serializers.ValidationError("User account is disabled")
            attrs['user'] = user
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this phone number does not exist")

        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=17)
    code = serializers.CharField(max_length=6, min_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate_phone(self, value):
        return validate_phone_number(value)

    def validate_code(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Code must contain only digits")
        return value

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value


class UserProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'email', 'default_shipping_address', 'date_joined']
        read_only_fields = ['id', 'phone', 'date_joined']

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value


class UpdateProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'default_shipping_address']

    def validate_email(self, value):
        if value and User.objects.filter(email=value).exclude(pk=self.instance.pk).exists():
            raise serializers.ValidationError("User with this email already exists")
        return value