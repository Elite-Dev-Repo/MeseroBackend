from users.serializers import ResendOTPSerializer
from users.serializers import VerifyUserEmailSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from users.serializers import UserProfileSerializer
from django.shortcuts import render
from .serializers import UserSerializer, OTPTokenSerializer
from .models import User, OTPToken
from rest_framework import generics
from rest_framework import status
from rest_framework.views import APIView
from django.utils import timezone
from django.db import transaction


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

class GetUserProfileAPIView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]


    def get_object(self):
        user_id = self.request.user.id
        user = User.objects.prefetch_related("restaurants").get(id=user_id)
        return user


