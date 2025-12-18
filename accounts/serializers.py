from rest_framework import serializers
from accounts.models import CustomUser
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings
from django.utils import timezone
from accounts.utils import email_verification_token
from rest_framework.exceptions import AuthenticationFailed


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password']

    def create(self, validated_data):
        request = self.context.get('request')

        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            is_verified=False
        )

        # 🔐 Generate token
        token = email_verification_token.make_token(user)

        # ⏱ Save time (used later for expiry)
        user.verification_sent_at = timezone.now()
        user.save()

        # 🌍 CURRENT SERVER URL (no localhost)
        verify_url = request.build_absolute_uri(
            reverse('verify-email')
        ) + f"?token={token}&email={user.email}"

        # 📧 Send email
        send_mail(
            subject="Verify your email",
            message=f"Click the link to verify your email:\n{verify_url}",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )

        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(
            email=data['email'],
            password=data['password']
        )

        if not user:
            raise AuthenticationFailed("Invalid email or password")

        if not user.is_verified:
            raise AuthenticationFailed(
                "Email is not verified. Verification link has been sent to registerd email."
            )

        return user


class AdminSignupSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password']

    def create(self, validated_data):
        validated_data['is_admin'] = True
        return CustomUser.objects.create_user(**validated_data)

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if not user.is_admin:
            raise serializers.ValidationError('You are not an admin user')
        return user


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    new_password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True, min_length=6)

    def validate(self, data):
        if data['new_password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def save(self):
        email = self.validated_data['email']
        new_password = self.validated_data['new_password']

        user = CustomUser.objects.get(email=email)
        user.set_password(new_password)
        user.save()
        return user