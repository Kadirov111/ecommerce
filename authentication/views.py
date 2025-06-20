from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from django.contrib.auth import get_user_model
from django.utils import timezone



from .models import  SMSVerification,BlacklistedToken
from .serializers import (
AuthorizeSerializer,VerifySerializer,LoginSerializer,LogoutSerializer,RefreshTokenSerializer,
ForgotPasswordSerializer,ResetPasswordSerializer,UserSerializer
)
from .utils import send_sms

User = get_user_model


@api_view(['POST'])
@permission_classes([AllowAny])
def authorize(request):
    serializer = AuthorizeSerializer(data=request.data)
    if serializer.is_valid():
        phone = serializer.validate_data['phone']

        sms_verification = SMSVerification.objects.create(
            phone=phone,
            verification_type='registration'
        )
        sms_verification .generate_code()
        sms_verification.save()

        send_sms(phone,sms_verification.code)

        return Response({
            'success': False,
            'error': {
                'code': 'INVALID_REQUEST',
                'message': 'The provided data is invalid',
                'details': serializer.errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)
