
from rest_framework import serializers
from .models import User, OTPToken
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.encoding import force_bytes, smart_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode



class UserSerializer(serializers.ModelSerializer):
    name = serializers.CharField(write_only=True, required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    gender = serializers.ChoiceField(
        choices=User.GENDER_CHOICES, required=False, allow_blank=True
    )

    class Meta:
        model = User
        fields = ["id", "email", "name", "first_name", "last_name", "gender", "password"]
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, attrs):
        name = attrs.pop("name", "").strip()
        if name:
            parts = name.split(None, 1)
            attrs["first_name"] = parts[0]
            attrs["last_name"] = parts[1] if len(parts) > 1 else ""
        elif not attrs.get("first_name"):
            raise serializers.ValidationError({"name": "This field is required."})

        attrs.setdefault("first_name", "")
        attrs.setdefault("last_name", "")
        return attrs

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    from restaurants.serializers import RestaurantDetailSerializer
    restaurants = RestaurantDetailSerializer(many=True, read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "first_name", "last_name", "gender", "restaurants"]
        read_only_fields = ["id", "email", "restaurants"]

    def get_name(self, obj):
        full_name = f"{obj.first_name} {obj.last_name}".strip()
        return full_name or obj.email.split("@")[0]



class OTPTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model =OTPToken
        fields = ["user", "token", "created_at", "expires"]


class VerifyUserEmailSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)



class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    class Meta:
            fields = ["email"]

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
   
   
    class Meta:
        fields = ["email"]

class ChangePasswordSerializer(serializers.Serializer):
    uidbs4 = serializers.CharField(min_length=1)
    token = serializers.CharField(min_length=1)
    new_password = serializers.CharField(min_length=6, max_length=128, write_only=True)
    confirm_password = serializers.CharField(min_length=6, max_length=128, write_only=True)

    class Meta:
        fields = ["uidbs4", "token", "new_password", "confirm_password"]

    def validate(self, attrs):
        uidbs4 = attrs.get("uidbs4")
        token = attrs.get("token")
        new_password = attrs.get("new_password")
        confirm_password = attrs.get("confirm_password")

        try:
            uid = urlsafe_base64_decode(uidbs4).decode()
            user = User.objects.get(id=uid)
        except (TypeError, ValueError, OverflowError, DjangoUnicodeDecodeError, User.DoesNotExist):
            raise serializers.ValidationError({"token": "Invalid or expired password reset link."})

        if not PasswordResetTokenGenerator().check_token(user, token):
            raise serializers.ValidationError({"token": "Invalid or expired password reset link."})

        if new_password != confirm_password:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})

        try:
            validate_password(new_password, user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})

        attrs["user"] = user
        return attrs