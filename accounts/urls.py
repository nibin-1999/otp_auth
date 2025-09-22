from django.urls import path
from accounts.views import request_otp, verify_otp


app_name = 'accounts'


urlpatterns = [
    path('request-otp/', request_otp, name='request-otp'),
    path('verify-otp/', verify_otp, name='verify-otp'),
]
