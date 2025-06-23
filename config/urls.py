from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

urlpatterns = [
    # Admin panel
    path('admin/', admin.site.urls),
    
    # API routes
    path('api/v1/auth/', include('auth.urls')),
    path('api/v1/', include('shop.urls')),
    
    path('health/', lambda request: HttpResponse('OK')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)