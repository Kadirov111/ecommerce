from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging
from .sms_service import sms_service
from .models import OTPVerification, UserLoginAttempt

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_otp_sms(self, phone, otp_code, otp_type):
    """Send OTP SMS asynchronously"""
    try:
        success, result = sms_service.send_otp(phone, otp_code, otp_type)

        if not success:
            logger.error(f"Failed to send OTP SMS to {phone}: {result}")
            # Retry with exponential backoff
            raise self.retry(countdown=60 * (2 ** self.request.retries))

        logger.info(f"OTP SMS sent successfully to {phone}")
        return {"success": True, "message_id": result}

    except Exception as e:
        logger.error(f"Error sending OTP SMS: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        else:
            return {"success": False, "error": str(e)}


@shared_task(bind=True, max_retries=3)
def send_custom_sms(self, phone, message):
    """Send custom SMS asynchronously"""
    try:
        success, result = sms_service.send_custom_message(phone, message)

        if not success:
            logger.error(f"Failed to send SMS to {phone}: {result}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))

        logger.info(f"SMS sent successfully to {phone}")
        return {"success": True, "message_id": result}

    except Exception as e:
        logger.error(f"Error sending SMS: {e}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        else:
            return {"success": False, "error": str(e)}


@shared_task
def cleanup_expired_otps():
    """Clean up expired OTP records"""
    try:
        # Delete OTPs older than 24 hours
        cutoff_time = timezone.now() - timedelta(hours=24)

        deleted_count = OTPVerification.objects.filter(
            created_at__lt=cutoff_time
        ).delete()[0]

        logger.info(f"Cleaned up {deleted_count} expired OTP records")
        return {"deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Error cleaning up expired OTPs: {e}")
        return {"error": str(e)}


@shared_task
def cleanup_old_login_attempts():
    """Clean up old login attempt records"""
    try:
        # Delete login attempts older than 7 days
        cutoff_time = timezone.now() - timedelta(days=7)

        deleted_count = UserLoginAttempt.objects.filter(
            attempt_time__lt=cutoff_time
        ).delete()[0]

        logger.info(f"Cleaned up {deleted_count} old login attempt records")
        return {"deleted_count": deleted_count}

    except Exception as e:
        logger.error(f"Error cleaning up old login attempts: {e}")
        return {"error": str(e)}


@shared_task
def send_welcome_sms(phone, name):
    """Send welcome SMS to new users"""
    try:
        message = f"Welcome to our platform, {name}! Your account has been successfully created."

        success, result = sms_service.send_custom_message(phone, message)

        if success:
            logger.info(f"Welcome SMS sent to {phone}")
        else:
            logger.error(f"Failed to send welcome SMS to {phone}: {result}")

        return {"success": success, "result": result}

    except Exception as e:
        logger.error(f"Error sending welcome SMS: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def send_security_alert_sms(phone, message):
    """Send security alert SMS"""
    try:
        success, result = sms_service.send_custom_message(phone, message)

        if success:
            logger.info(f"Security alert SMS sent to {phone}")
        else:
            logger.error(f"Failed to send security alert SMS to {phone}: {result}")

        return {"success": success, "result": result}

    except Exception as e:
        logger.error(f"Error sending security alert SMS: {e}")
        return {"success": False, "error": str(e)}


@shared_task
def generate_daily_stats():
    """Generate daily authentication statistics"""
    try:
        today = timezone.now().date()
        start_of_day = timezone.datetime.combine(today, timezone.datetime.min.time())
        end_of_day = timezone.datetime.combine(today, timezone.datetime.max.time())

        # Make timezone aware
        start_of_day = timezone.make_aware(start_of_day)
        end_of_day = timezone.make_aware(end_of_day)

        # Count OTPs sent today
        otps_sent = OTPVerification.objects.filter(
            created_at__range=[start_of_day, end_of_day]
        ).count()

        # Count successful logins today
        successful_logins = UserLoginAttempt.objects.filter(
            attempt_time__range=[start_of_day, end_of_day],
            success=True
        ).count()

        # Count failed logins today
        failed_logins = UserLoginAttempt.objects.filter(
            attempt_time__range=[start_of_day, end_of_day],
            success=False
        ).count()

        stats = {
            "date": today.isoformat(),
            "otps_sent": otps_sent,
            "successful_logins": successful_logins,
            "failed_logins": failed_logins,
            "login_success_rate": (successful_logins / (successful_logins + failed_logins)) * 100 if (
                                                                                                                 successful_logins + failed_logins) > 0 else 0
        }

        logger.info(f"Daily stats generated: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Error generating daily stats: {e}")
        return {"error": str(e)}