from rest_framework import serializers
from django.contrib.ayth import authenticate
from .models import  User,SMSVerification

class AuthorizeSerializer(serializers.Serializers):
    phone = serializers.CharField(max_length=20)
    password = serializers.CharField(write_only=True,required=False)


    def validate_phone(self,value):
        if not value.startswitch('+'):
            raise serializers.ValidationError("Phone number must include country code")
        return value


class VerifySerializer(serializers.Serializers):
    phone = serializers.CharField(max_legth=20)
    code = serializers.CharField(max_legth=6)
    password = serializers.CharField(write_only=True,required=False)
    name = serializers.CharField(max_length=100,required=False)

    def validate_phone(self,value):
        if not value.startswitch('+'):
            raise  serializers.ValidationError("Phone nuber must include country code")
        return value


class LoginSerializer(serializers.Serializers):
    phone = serializers.CharField(max_length=20 )
    password = serializers.CharField(write_only=True)

    def validate(self,data):
        phone = data.get('phone')
        password = data.get('password')

        if phone and password:
            user = authenticate(username=phone,password=password)
            if not user:
                raise serializers.ValidationError("Invalid credentials")
            if not user.is_verified:
                raise  serializers.ValidationError("Account not verified")
            data['user']=user
        else:
            raise serializers.ValidationError('Must include phone and password')
        return data


class LogoutSerializer(serializers.Serializers):
    refresh_token = serializers.CharField()

class RefreshTokenSerializer(serializers.Serializers):
    refresh_token = serializers.CharField()

class ForgotPasswordSerializer(serializers.Serializers):
    phone = serializers.CharField(max_legth=20)

    def validate_phone(self,value):
        if not value.startswitch('+'):
            raise serializers.ValidationError("Phone number must include country code")
        if not User.objects.filter(phone=value).exists():
            raise serializers.ValidationError("User with this phone number does not exist")
        return value

class ResetPasswordSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=20)
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, min_length=8)

    def validate_phone(self, value):
        if not value.startswith('+'):
            raise serializers.ValidationError("Phone number must include country code")
        return value


class UserSerializer(serializers.Serializers):
    class Meta:
        model = User
        fields = ['id', 'phone', 'name', 'email', 'default_shipping_address', 'date_joined']
        read_only_fields = ['id', 'phone', 'date_joined']