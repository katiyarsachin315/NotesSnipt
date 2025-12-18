from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authtoken.models import Token
from accounts.models import CustomUser
from accounts.serializers import SignupSerializer, LoginSerializer, AdminSignupSerializer, AdminLoginSerializer, ForgotPasswordSerializer, ResetPasswordSerializer
from accounts.utils import email_verification_token
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"message": "Account created. Please verify, Verification email sent to registered email id."},
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        token = request.GET.get('token')
        email = request.GET.get('email')

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "Invalid email"}, status=400)

        if email_verification_token.check_token(user, token):
            user.is_verified = True
            user.save()
            return Response({"message": "Email verified successfully"}, status=200)

        return Response({"error": "Invalid token"}, status=400)


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data
            token, _ = Token.objects.get_or_create(user=user)

            return Response({
                "id": user.id,
                "full_name": user.full_name,
                "email": user.email,
                "token": token.key
            }, status=200)

        # 🔁 HANDLE UNVERIFIED USER
        errors = serializer.errors

        if "email_not_verified" in errors:
            try:
                user = CustomUser.objects.get(email=request.data.get("email"))

                token = email_verification_token.make_token(user)
                user.verification_sent_at = timezone.now()
                user.save()

                verify_url = request.build_absolute_uri(
                    reverse('verify-email')
                ) + f"?token={token}"

                send_mail(
                    subject="Verify your email",
                    message=f"Click the link to verify your email:\n{verify_url}",
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                )

            except CustomUser.DoesNotExist:
                pass

        return Response(errors, status=400)

class AdminSignupView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_admin:
            return Response({"error": "Only admin can create another admin"}, status=403)
        serializer = AdminSignupSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Admin user created"}, status=201)
        return Response(serializer.errors, status=400)

class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data
            token, created = Token.objects.get_or_create(user=user)
            return Response({"token": token.key}, status=200)
        return Response(serializer.errors, status=400)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        if serializer.is_valid():
            return Response({"message": "Email verified. You can now reset your password.","email_verified": True}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self,request):
        serializer = ResetPasswordSerializer(data=request.dat)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response({"message": "Password reset successful!"}, status=status.HTTP_200_OK)
            except CustomUser.DoesNotExist:
                return Response({"error": "User with this email does not exist."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
