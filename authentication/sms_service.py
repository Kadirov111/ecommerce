import logging
import requests
from django.conf import settings
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class SMSProvider(ABC):

    @abstractmethod
    def send_sms(self, phone, message):
        pass


class TwilioSMSProvider(SMSProvider):
    def __init__(self):
        self.account_sid = settings.SMS_SERVICE_CONFIG.get('API_KEY')
        self.auth_token = settings.SMS_SERVICE_CONFIG.get('API_SECRET')
        self.from_number = settings.SMS_SERVICE_CONFIG.get('FROM_NUMBER')

        if not all([self.account_sid, self.auth_token, self.from_number]):
            raise ValueError("Twilio configuration incomplete")

    def send_sms(self, phone, message):
        try:
            from twilio.rest import Client

            client = Client(self.account_sid, self.auth_token)

            message = client.messages.create(
                body=message,
                from_=self.from_number,
                to=phone
            )

            logger.info(f"SMS sent via Twilio to {phone}, SID: {message.sid}")
            return True, message.sid

        except Exception as e:
            logger.error(f"Failed to send SMS via Twilio: {e}")
            return False, str(e)


class EskizSMSProvider(SMSProvider):
    """Eskiz.uz SMS provider (Uzbekistan)"""

    def __init__(self):
        self.api_key = settings.SMS_SERVICE_CONFIG.get('API_KEY')
        self.api_secret = settings.SMS_SERVICE_CONFIG.get('API_SECRET')
        self.base_url = "https://notify.eskiz.uz/api"
        self.token = None

        if not all([self.api_key, self.api_secret]):
            raise ValueError("Eskiz configuration incomplete")

    def _get_token(self):
        """Get authentication token"""
        try:
            response = requests.post(
                f"{self.base_url}/auth/login",
                data={
                    'email': self.api_key,
                    'password': self.api_secret
                }
            )

            if response.status_code == 200:
                data = response.json()
                self.token = data.get('data', {}).get('token')
                return True
            else:
                logger.error(f"Failed to get Eskiz token: {response.text}")
                return False

        except Exception as e:
            logger.error(f"Error getting Eskiz token: {e}")
            return False

    def send_sms(self, phone, message):
        """Send SMS using Eskiz"""
        try:
            if not self.token and not self._get_token():
                return False, "Failed to authenticate"

            # Format phone for Uzbekistan
            if phone.startswith('+998'):
                phone = phone[1:]  # Remove + sign
            elif phone.startswith('998'):
                pass  # Already correct format
            else:
                phone = '998' + phone.lstrip('+')

            headers = {
                'Authorization': f'Bearer {self.token}',
                'Content-Type': 'application/json'
            }

            data = {
                'mobile_phone': phone,
                'message': message,
                'from': '4546'  # Default sender for Eskiz
            }

            response = requests.post(
                f"{self.base_url}/message/sms/send",
                json=data,
                headers=headers
            )

            if response.status_code == 200:
                result = response.json()
                if result.get('status') == 'success':
                    logger.info(f"SMS sent via Eskiz to {phone}")
                    return True, result.get('id')
                else:
                    logger.error(f"Eskiz SMS failed: {result}")
                    return False, result.get('message', 'Unknown error')
            else:
                logger.error(f"Eskiz API error: {response.text}")
                return False, response.text

        except Exception as e:
            logger.error(f"Failed to send SMS via Eskiz: {e}")
            return False, str(e)


class PlayMobileSMSProvider(SMSProvider):
    """PlayMobile SMS provider"""

    def __init__(self):
        self.api_key = settings.SMS_SERVICE_CONFIG.get('API_KEY')
        self.api_secret = settings.SMS_SERVICE_CONFIG.get('API_SECRET')
        self.base_url = "https://send.smsxabar.uz/broker-api"

        if not all([self.api_key, self.api_secret]):
            raise ValueError("PlayMobile configuration incomplete")

    def send_sms(self, phone, message):
        """Send SMS using PlayMobile"""
        try:
            # Format phone for Uzbekistan
            if phone.startswith('+998'):
                phone = phone[4:]  # Remove +998
            elif phone.startswith('998'):
                phone = phone[3:]  # Remove 998

            data = {
                'messages': [{
                    'recipient': phone,
                    'message-id': f"msg_{phone}_{int(timezone.now().timestamp())}",
                    'sms': {
                        'originator': '3700',
                        'content': {
                            'text': message
                        }
                    }
                }]
            }

            headers = {
                'Authorization': f'Basic {self.api_key}:{self.api_secret}',
                'Content-Type': 'application/json'
            }

            response = requests.post(
                f"{self.base_url}/send",
                json=data,
                headers=headers
            )

            if response.status_code == 200:
                logger.info(f"SMS sent via PlayMobile to {phone}")
                return True, response.json()
            else:
                logger.error(f"PlayMobile API error: {response.text}")
                return False, response.text

        except Exception as e:
            logger.error(f"Failed to send SMS via PlayMobile: {e}")
            return False, str(e)


class MockSMSProvider(SMSProvider):
    """Mock SMS provider for development"""

    def send_sms(self, phone, message):
        """Mock SMS sending - just log the message"""
        logger.info(f"MOCK SMS to {phone}: {message}")
        print(f"📱 MOCK SMS to {phone}: {message}")
        return True, "mock_message_id"


class SMSService:
    """SMS service manager"""

    def __init__(self):
        self.provider = self._get_provider()

    def _get_provider(self):
        """Get SMS provider based on configuration"""
        config = settings.SMS_SERVICE_CONFIG

        # Use mock provider in development or when mock mode is enabled
        if config.get('MOCK_MODE', False):
            return MockSMSProvider()

        provider_name = config.get('PROVIDER', 'twilio').lower()

        providers = {
            'twilio': TwilioSMSProvider,
            'eskiz': EskizSMSProvider,
            'playmobile': PlayMobileSMSProvider,
        }

        provider_class = providers.get(provider_name)
        if not provider_class:
            raise ValueError(f"Unknown SMS provider: {provider_name}")

        return provider_class()

    def send_otp(self, phone, otp_code, otp_type):
        """Send OTP code via SMS"""
        messages = {
            'registration': f"Your verification code is: {otp_code}. Valid for 5 minutes.",
            'login': f"Your login code is: {otp_code}. Valid for 5 minutes.",
            'password_reset': f"Your password reset code is: {otp_code}. Valid for 5 minutes.",
        }

        message = messages.get(otp_type, f"Your verification code is: {otp_code}")

        try:
            success, result = self.provider.send_sms(phone, message)

            if success:
                logger.info(f"OTP sent successfully to {phone}")
            else:
                logger.error(f"Failed to send OTP to {phone}: {result}")

            return success, result

        except Exception as e:
            logger.error(f"SMS service error: {e}")
            return False, str(e)

    def send_custom_message(self, phone, message):
        try:
            return self.provider.send_sms(phone, message)
        except Exception as e:
            logger.error(f"Failed to send custom SMS: {e}")
            return False, str(e)


sms_service = SMSService()