import re
import logging
from django.conf import settings
from django.utils import timezone
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from datetime import timedelta
from .models import OTPVerification, UserLoginAttempt

logger = logging.getLogger(__name__)


def validate_phone_number(phone):
    phone = re.sub(r'[^\d+]', '', phone)

    if not re.match(r'^\+?1?\d{9,15}$', phone):
        from rest_framework import serializers
        raise serializers.ValidationError("Invalid phone number format")

    if not phone.startswith('+'):
        phone = '+' + phone

    return phone


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def get_user_agent(request):
    return request.META.get('HTTP_USER_AGENT', '')


def can_request_otp(phone, otp_type):
    cooldown_minutes = getattr(settings, 'OTP_CONFIG', {}).get('RESEND_COOLDOWN_MINUTES', 1)
    cooldown_time = timezone.now() - timedelta(minutes=cooldown_minutes)

    recent_otp = OTPVerification.objects.filter(
        phone=phone,
        otp_type=otp_type,
        created_at__gt=cooldown_time
    ).first()

    return recent_otp is None


def create_otp_verification(phone, otp_type, user_data=None):
    OTPVerification.objects.filter(
        phone=phone,
        otp_type=otp_type,
        is_used=False
    ).update(is_used=True)

    otp_code = OTPVerification.generate_otp()

    otp_verification = OTPVerification.objects.create(
        phone=phone,
        otp_code=otp_code,
        otp_type=otp_type,
        user_data=user_data
    )

    return otp_verification


def verify_otp(phone, code, otp_type):
    try:
        otp_verification = OTPVerification.objects.get(
            phone=phone,
            otp_code=code,
            otp_type=otp_type,
            is_used=False
        )

        if otp_verification.is_expired():
            return False, "OTP has expired"

        if not otp_verification.can_attempt():
            return False, "Maximum verification attempts reached"

        otp_verification.mark_as_used()

        return True, otp_verification

    except OTPVerification.DoesNotExist:
        otp_record = OTPVerification.objects.filter(
            phone=phone,
            otp_type=otp_type,
            is_used=False
        ).first()

        if otp_record:
            otp_record.increment_attempts()

        return False, "Invalid OTP code"


def record_login_attempt(phone, ip_address, user_agent, success=False):
    try:
        UserLoginAttempt.objects.create(
            phone=phone,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success
        )
    except Exception as e:
        logger.error(f"Failed to record login attempt: {e}")


def is_account_locked(phone, ip_address=None):
    failed_attempts = UserLoginAttempt.objects.filter(
        phone=phone,
        success=False,
        attempt_time__gt=timezone.now() - timedelta(hours=1)
    ).count()

    if failed_attempts >= 5:
        return True, "Account temporarily locked due to multiple failed attempts"

    if ip_address:
        ip_failed_attempts = UserLoginAttempt.objects.filter(
            ip_address=ip_address,
            success=False,
            attempt_time__gt=timezone.now() - timedelta(hours=1)
        ).count()

        if ip_failed_attempts >= 10:
            return True, "IP address temporarily blocked due to multiple failed attempts"

    return False, None


def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is not None:
        custom_response_data = {
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'The provided data is invalid',
                'details': {}
            }
        }

        if hasattr(exc, 'detail'):
            if isinstance(exc.detail, dict):
                for field, messages in exc.detail.items():
                    if isinstance(messages, list):
                        custom_response_data['error']['details'][field] = messages[0]
                    else:
                        custom_response_data['error']['details'][field] = str(messages)
            elif isinstance(exc.detail, list):
                custom_response_data['error']['message'] = exc.detail[0]
            else:
                custom_response_data['error']['message'] = str(exc.detail)

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            custom_response_data['error']['code'] = 'UNAUTHORIZED'
            custom_response_data['error']['message'] = 'Authentication credentials were not provided or are invalid'
        elif response.status_code == status.HTTP_403_FORBIDDEN:
            custom_response_data['error']['code'] = 'FORBIDDEN'
            custom_response_data['error']['message'] = 'You do not have permission to perform this action'
        elif response.status_code == status.HTTP_404_NOT_FOUND:
            custom_response_data['error']['code'] = 'NOT_FOUND'
            custom_response_data['error']['message'] = 'The requested resource was not found'
        elif response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
            custom_response_data['error']['code'] = 'RATE_LIMIT_EXCEEDED'
            custom_response_data['error']['message'] = 'Too many requests, please try again later'

        response.data = custom_response_data

    return response


def create_success_response(data=None, message=None, status_code=status.HTTP_200_OK):
    response_data = {'success': True}

    if data is not None:
        response_data['data'] = data

    if message:
        response_data['message'] = message

    return Response(response_data, status=status_code)


def create_error_response(message, code='INVALID_REQUEST', details=None, status_code=status.HTTP_400_BAD_REQUEST):
    response_data = {
        'success': False,
        'error': {
            'code': code,
            'message': message
        }
    }

    if details:
        response_data['error']['details'] = details

    return Response(response_data, status=status_code)


def mask_phone_number(phone):
    if len(phone) <= 4:
        return phone
    return phone[:-4] + '****'


def format_phone_display(phone):
    if phone.startswith('+'):
        return phone
    return f'+{phone}'