from django.urls import path
from . import views

app_name = 'authentication'

urlpatterns = [
    path('authorize/', views.authorize, name='authorize'),
    path('verify/', views.verify, name='verify'),
    path('login/', views.login, name='login'),
    path('logout/', views.logout, name='logout'),
    path('token/refresh/', views.refresh_token, name='refresh_token'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('reset-password/', views.reset_password, name='reset_password'),
]