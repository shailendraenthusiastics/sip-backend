from decimal import Decimal

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import AffiliateClick, Calculation, Lead

User = get_user_model()


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def validate_email(self, value):
        if value and User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if value and User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username = serializers.CharField(required=False, write_only=True)
    username_or_email = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # TokenObtainPairSerializer injects USERNAME_FIELD as required by default.
        # We authenticate via username_or_email, so relax that inherited field.
        if self.username_field in self.fields:
            self.fields[self.username_field].required = False
            self.fields[self.username_field].allow_blank = True

    def validate(self, attrs):
        identifier = attrs.pop("username_or_email", None) or attrs.get("username")
        password = attrs.get("password")

        if not identifier:
            raise serializers.ValidationError(
                {"username_or_email": ["This field is required."]}
            )

        user = (
            User.objects.filter(username__iexact=identifier).first()
            or User.objects.filter(email__iexact=identifier).first()
        )
        if user is None:
            raise serializers.ValidationError(
                "No active account found with the given credentials."
            )

        attrs[self.username_field] = user.username
        attrs["password"] = password
        data = super().validate(attrs)
        data["user"] = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "is_staff": user.is_staff,
        }
        return data


class SIPRequestSerializer(serializers.Serializer):
    monthly_investment = serializers.DecimalField(max_digits=14, decimal_places=2)
    annual_interest_rate = serializers.DecimalField(max_digits=6, decimal_places=2)
    years = serializers.IntegerField(min_value=1)

    def validate_monthly_investment(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                "Monthly investment must be greater than zero."
            )
        return value

    def validate_annual_interest_rate(self, value):
        if value < 0:
            raise serializers.ValidationError("Interest rate cannot be negative.")
        return value


class CalculationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Calculation
        fields = ["id", "amount", "rate", "time", "result", "created_at"]
        read_only_fields = ["id", "result", "created_at"]


class AffiliateClickSerializer(serializers.ModelSerializer):
    class Meta:
        model = AffiliateClick
        fields = [
            "id",
            "source",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class LeadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lead
        fields = [
            "id",
            "email",
            "source",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "utm_content",
            "consent_given",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_email(self, value):
        return value.lower().strip()

    def validate_consent_given(self, value):
        if value is not True:
            raise serializers.ValidationError("Consent is required to save your email.")
        return value
