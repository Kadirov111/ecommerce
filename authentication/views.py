from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import authenticate
from django.core.cache import cache
from django.conf import settings
from celery import shared_task
import random
import string
import requests
from datetime import timedelta
from django.utils import timezone

from .models import User
from .serializers import (
    AuthorizeSerializer,
    VerifySerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer
)


@shared_task
def send_sms_task(phone_number, message):
    try:
        api_url = settings.SMS_API_URL
        api_key = settings.SMS_API_KEY

        payload = {
            'to': phone_number,
            'text': message,
            'api_key': api_key
        }

        response = requests.post(api_url, json=payload, timeout=30)

        if response.status_code == 200:
            return {'success': True, 'message': 'SMS sent successfully'}
        else:
            return {'success': False, 'error': f'SMS service error: {response.status_code}'}

    except requests.exceptions.RequestException as e:
        return {'success': False, 'error': f'Network error: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Unexpected error: {str(e)}'}


def generate_otp_code():
    return ''.join(random.choices(string.digits, k=6))


def get_cache_key(phone, action_type):
    return f"otp_{action_type}_{phone.replace('+', '')}"


@api_view(['POST'])
@permission_classes([AllowAny])
def authorize_view(request):
    serializer = AuthorizeSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'The provided data is invalid',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    phone = serializer.validated_data['phone']
    password = serializer.validated_data.get('password')

    otp_code = generate_otp_code()

    cache_key = get_cache_key(phone, 'register' if password else 'login')
    cache_data = {
        'code': otp_code,
        'phone': phone,
        'password': password,
        'attempts': 0,
        'created_at': timezone.now().isoformat()
    }
    cache.set(cache_key, cache_data, timeout=300)  # 5 minutes

    message = f"Your verification code is: {otp_code}. Valid for 5 minutes."
    send_sms_task.delay(phone, message)

    return Response({
        'success': True,
        'message': f'Verification code sent to {phone}'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_view(request):
    serializer = VerifySerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'The provided data is invalid',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    phone = serializer.validated_data['phone']
    code = serializer.validated_data['code']
    password = serializer.validated_data.get('password')
    name = serializer.validated_data.get('name')

    # Check both register and login cache keys
    register_cache_key = get_cache_key(phone, 'register')
    login_cache_key = get_cache_key(phone, 'login')

    cached_data = cache.get(register_cache_key) or cache.get(login_cache_key)

    if not cached_data:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Verification code expired or invalid',
                'details': {'field': 'code', 'message': 'Verification code expired'}
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    if cached_data.get('attempts', 0) >= 3:
        cache.delete(register_cache_key)
        cache.delete(login_cache_key)
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Too many failed attempts',
                'details': {'field': 'code', 'message': 'Maximum attempts exceeded'}
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    if cached_data['code'] != code:
        cached_data['attempts'] = cached_data.get('attempts', 0) + 1
        cache.set(register_cache_key if password else login_cache_key,
                  cached_data, timeout=300)

        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Invalid verification code',
                'details': {'field': 'code', 'message': 'Verification code is incorrect'}
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    cache.delete(register_cache_key)
    cache.delete(login_cache_key)

    user_exists = User.objects.filter(phone=phone).exists()

    if password and not user_exists:
        user = User.objects.create_user(
            phone=phone,
            password=password,
            name=name or ''
        )
    elif user_exists:
        user = User.objects.get(phone=phone)
    else:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'User not found',
                'details': {'field': 'phone', 'message': 'User with this phone number does not exist'}
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    return Response({
        'success': True,
        'data': {
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'expires_in': settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'The provided data is invalid',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    phone = serializer.validated_data['phone']
    password = serializer.validated_data['password']

    user = authenticate(phone=phone, password=password)

    if not user:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_CREDENTIALS',
                'message': 'Invalid phone number or password',
                'details': {'field': 'credentials', 'message': 'Phone number or password is incorrect'}
            }
        }, status=status.HTTP_401_UNAUTHORIZED)

    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token

    return Response({
        'success': True,
        'data': {
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'expires_in': settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
        }
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    serializer = LogoutSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'The provided data is invalid',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh_token = serializer.validated_data['refresh_token']
        token = RefreshToken(refresh_token)
        token.blacklist()

        return Response({
            'success': True,
            'message': 'Successfully logged out'
        }, status=status.HTTP_200_OK)

    except TokenError:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid or expired refresh token',
                'details': {'field': 'refresh_token', 'message': 'Token is invalid or expired'}
            }
        }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    serializer = RefreshTokenSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'The provided data is invalid',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        refresh_token = serializer.validated_data['refresh_token']
        token = RefreshToken(refresh_token)
        new_access_token = token.access_token

        return Response({
            'success': True,
            'data': {
                'access_token': str(new_access_token),
                'expires_in': settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'].total_seconds()
            }
        }, status=status.HTTP_200_OK)

    except TokenError:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_TOKEN',
                'message': 'Invalid or expired refresh token',
                'details': {'field': 'refresh_token', 'message': 'Token is invalid or expired'}
            }
        }, status=status.HTTP_401_UNAUTHORIZED)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password_view(request):
    serializer = ForgotPasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'The provided data is invalid',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    phone = serializer.validated_data['phone']

    # Check if user exists
    if not User.objects.filter(phone=phone).exists():
        return Response({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User with this phone number does not exist',
                'details': {'field': 'phone', 'message': 'User not found'}
            }
        }, status=status.HTTP_404_NOT_FOUND)

    otp_code = generate_otp_code()

    cache_key = get_cache_key(phone, 'reset_password')
    cache_data = {
        'code': otp_code,
        'phone': phone,
        'attempts': 0,
        'created_at': timezone.now().isoformat()
    }
    cache.set(cache_key, cache_data, timeout=300)  # 5 minutes

    message = f"Your password reset code is: {otp_code}. Valid for 5 minutes."
    send_sms_task.delay(phone, message)

    return Response({
        'success': True,
        'message': f'Password reset code sent to {phone}'
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def reset_password_view(request):
    serializer = ResetPasswordSerializer(data=request.data)

    if not serializer.is_valid():
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'The provided data is invalid',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    phone = serializer.validated_data['phone']
    code = serializer.validated_data['code']
    new_password = serializer.validated_data['new_password']

    cache_key = get_cache_key(phone, 'reset_password')
    cached_data = cache.get(cache_key)

    if not cached_data:
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Verification code expired or invalid',
                'details': {'field': 'code', 'message': 'Verification code expired'}
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    if cached_data.get('attempts', 0) >= 3:
        cache.delete(cache_key)
        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Too many failed attempts',
                'details': {'field': 'code', 'message': 'Maximum attempts exceeded'}
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    if cached_data['code'] != code:
        cached_data['attempts'] = cached_data.get('attempts', 0) + 1
        cache.set(cache_key, cached_data, timeout=300)

        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'Invalid verification code',
                'details': {'field': 'code', 'message': 'Verification code is incorrect'}
            }
        }, status=status.HTTP_400_BAD_REQUEST)

    cache.delete(cache_key)

    try:
        user = User.objects.get(phone=phone)
        user.set_password(new_password)
        user.save()

        return Response({
            'success': True,
            'message': 'Password reset successful'
        }, status=status.HTTP_200_OK)

    except User.DoesNotExist:
        return Response({
            'success': False,
            'error': {
                'code': 'USER_NOT_FOUND',
                'message': 'User not found',
                'details': {'field': 'phone', 'message': 'User with this phone number does not exist'}
            }
        }, status=status.HTTP_404_NOT_FOUND)