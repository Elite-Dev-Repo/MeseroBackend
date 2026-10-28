from django.urls import path
from .views import CreateUserAPIView,GetUserProfileAPIView, VerifyUserEmailAPIView, ResendOTPForEmailVerification

urlpatterns = [
    path("create-user/", CreateUserAPIView.as_view()),
    path("verify-email/", VerifyUserEmailAPIView.as_view()),
    path("resend-otp/", ResendOTPForEmailVerification.as_view()),
    path("profile/", GetUserProfileAPIView.as_view())
]