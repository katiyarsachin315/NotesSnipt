from rest_framework import serializers
from accounts.models import CustomUser
from django.contrib.auth import authenticate
from django.conf import settings
from rest_framework.exceptions import AuthenticationFailed
from django.core.mail import EmailMultiAlternatives
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.template.loader import render_to_string
from notesapp.models import Note


class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = CustomUser
        fields = ['email', 'full_name', 'password']

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            email=validated_data['email'],
            full_name=validated_data['full_name'],
            password=validated_data['password'],
            is_verified=False,
            is_active=False   # 🔥 IMPORTANT
        )

        # 🔐 Generate uid + token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # 🔗 Frontend verification link
        verification_link = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"

        # 📧 HTML email
        html_content = render_to_string(
            'email/verify_email.html',
            {
                'user': user,
                'verification_link': verification_link
            }
        )

        email = EmailMultiAlternatives(
            subject="Verify Your Email - NotesSnipt",
            body="Please verify your email",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        email.attach_alternative(html_content, "text/html")
        email.send()

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


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("User with this email does not exist.")
        return value

    
class ResetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, min_length=6)
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        print("Data:",data)
        if data['password'] != data['confirm_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data
    
    
#Admin 

class AdminLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])

        if not user:
            raise serializers.ValidationError('Invalid email or password')

        if not (user.is_admin or user.is_superuser):
            raise serializers.ValidationError('You are not an admin user')

        if not user.is_verified:
            raise serializers.ValidationError('Email is not verified')
        
        if not user.is_active:
            raise serializers.ValidationError('Account is inactive')

        return user


# 🔹 NOTE (for listing)
class AdminNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'title', 'description', 'content', 'created_at']


# 🔹 USER (with nested notes)
class AdminUserSerializer(serializers.ModelSerializer):
    notes = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'full_name', 'is_verified', 'is_admin', 'notes']

    def get_notes(self, obj):
        notes = obj.notes.filter(is_deleted=False)
        return AdminNoteSerializer(notes, many=True).data


# 🔹 UPDATE USER
class AdminUserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['full_name', 'is_verified', 'is_admin']


# 🔹 UPDATE NOTE
class AdminNoteUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['title', 'description', 'content']