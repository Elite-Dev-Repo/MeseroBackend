from django.urls import path
from .views import CreateUserAPIView,GetUserProfileAPIView, VerifyUserEmailAPIView, ResendOTPForEmailVerification,RequestPasswordResetLinkAPIView,PasswordResetLinkAPIView,ChangePasswordAPIView

urlpatterns = [
    path("create-user/", CreateUserAPIView.as_view()),
    path("verify-email/", VerifyUserEmailAPIView.as_view()),
    path("forgot-password/", RequestPasswordResetLinkAPIView.as_view()),
    path("password/<uidbs4>/<token>/", PasswordResetLinkAPIView.as_view()),
    path("change-password/", ChangePasswordAPIView.as_view()),
    path("resend-otp/", ResendOTPForEmailVerification.as_view()),
    path("profile/", GetUserProfileAPIView.as_view())
]