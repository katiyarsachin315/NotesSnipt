from django.urls import path
from accounts.views import *

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('create-admin/', AdminSignupView.as_view(), name='create-admin'),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
    path('verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    # path('resend-verification/', ResendVerificationView.as_view()),
]