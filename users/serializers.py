
from rest_framework import serializers
from .models import User, OTPToken



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

    