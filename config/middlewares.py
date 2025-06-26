from django.contrib.auth.middleware import get_user
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.utils.functional import SimpleLazyObject


class AuthenticationMiddlewareJWT(MiddlewareMixin):
    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

    def __call__(self, request):
        # Lazy user loading
        request.user = SimpleLazyObject(lambda: self.get_user(request))
        return self.get_response(request)

    def get_user(self, request):
        # Avval session-based authentication tekshiramiz
        user = get_user(request)
        if user.is_authenticated:
            return user

        # Agar session user yo'q bo'lsa, JWT token tekshiramiz
        try:
            jwt_auth = JWTAuthentication()
            validated_token = jwt_auth.get_validated_token(
                jwt_auth.get_raw_token(jwt_auth.get_header(request))
            )
            if validated_token:
                user = jwt_auth.get_user(validated_token)
                return user
        except (InvalidToken, TokenError, TypeError, AttributeError):
            # Token noto'g'ri yoki mavjud emas
            pass
        except Exception:
            # Boshqa xatoliklar
            pass

        # Agar hech narsa topmasa, AnonymousUser qaytaramiz
        return AnonymousUser()