from users.serializers import ResendOTPSerializer
from users.serializers import VerifyUserEmailSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from users.serializers import UserProfileSerializer
from django.shortcuts import render
from .serializers import UserSerializer, OTPTokenSerializer, PasswordResetRequestSerializer,ChangePasswordSerializer
from .models import User, OTPToken
from rest_framework import generics
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, smart_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.core.mail import send_mail
from django.conf import settings
import logging
import os

logger = logging.getLogger(__name__)


# Create your views here.


class CreateUserAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]



class VerifyUserEmailAPIView(APIView):
    serializer_class = VerifyUserEmailSerializer
    def post(self, request):
        with transaction.atomic():
            req_code = request.data.get("code")
            req_email = request.data.get("email")
            if not OTPToken.objects.filter(user__email=req_email, token=req_code).exists():
                return Response({"error": "Invalid token or email inputed"}, status=status.HTTP_404_NOT_FOUND)
            otp = OTPToken.objects.filter(user__email=req_email, token=req_code).last()
            if otp.expires < timezone.now():
                return Response({"error": "Token expired, request for a new token"}, status=status.HTTP_400_BAD_REQUEST)
            user = otp.user
            user.is_active = True
            user.save()
            return Response({"success": "Email sucessfully verified."}, status=status.HTTP_200_OK) 


class ResendOTPForEmailVerification(APIView):
    serializer_class = ResendOTPSerializer
    permission_classes = [AllowAny]
    def post(self, request):
        req_email = request.data.get("email")

        if not User.objects.filter(email=req_email).exists():
            return Response({"success": "If an account with that email exists, an email will be sent to it."}, status=status.HTTP_200_OK)

        user = User.objects.get(email=req_email)
        if user.is_active == True:
            return Response({"error": "User email already verified."}, status=status.HTTP_200_OK)
        OTPToken.objects.create(user=user)
        return Response({"success": "If an account with that email exists, an email will be sent to it."}, status=status.HTTP_200_OK)


class RequestPasswordResetLinkAPIView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    throttle_scope = "password_reset"
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        generic_response = Response(
            {"message": "If a user with that email account exists, an email would be sent to it."},
            status=status.HTTP_200_OK,
        )
        if not User.objects.filter(email=email).exists():
            return generic_response
        user = User.objects.get(email=email)
        token = PasswordResetTokenGenerator().make_token(user)
        uidbs4 = urlsafe_base64_encode(smart_bytes(user.id))
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000").rstrip("/")
        mail_url = f"{base_url}/reset-password/{uidbs4}/{token}"

        subject = "Password Reset Request"
        body = (
            f"Hello {user.first_name},\n\n"
            "You requested a password reset. Use the link below to reset your password:\n"
            f"{mail_url}\n\n"
            "If you did not request this, you can safely ignore this email.\n"
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception:
            logger.exception("Failed to send password reset email to %s", user.email)
        return generic_response


class PasswordResetLinkAPIView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request, uidbs4, token):
        try:
            uid = urlsafe_base64_decode(uidbs4).decode()
            user = User.objects.get(id=uid)
        except (TypeError, ValueError, OverflowError, DjangoUnicodeDecodeError, User.DoesNotExist):
            return Response({"message": "Invalid password reset link"}, status=status.HTTP_400_BAD_REQUEST)
        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({"message": "Invalid password reset link - token"}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"message": "valid reset link"}, status=status.HTTP_200_OK)


class ChangePasswordAPIView(generics.GenericAPIView):

    serializer_class = ChangePasswordSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        return Response({"message": "password changed successfully."}, status=status.HTTP_200_OK)



class GetUserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]


    def get_object(self):
        user_id = self.request.user.id
        user = User.objects.prefetch_related("restaurants").get(id=user_id)
        return user


