from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authtoken.models import Token
from accounts.models import CustomUser

from accounts.serializers import SignupSerializer, LoginSerializer, ResetPasswordSerializer, AdminLoginSerializer, AdminUserUpdateSerializer, AdminUserSerializer
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.template.loader import render_to_string
from django.core.mail import EmailMultiAlternatives
from django.utils.encoding import force_bytes, force_str
from notesapp.permissions import IsAdminOnly
from rest_framework.pagination import PageNumberPagination
from notesapp.models import Note

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

    def get(self, request, uid, token):
        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = CustomUser.objects.get(pk=user_id)
        except Exception:
            return Response({"error": "Invalid user"}, status=status.HTTP_400_BAD_REQUEST)

        if not default_token_generator.check_token(user, token):
            return Response({"error": "Invalid or expired link"}, status=status.HTTP_400_BAD_REQUEST)

        user.is_verified = True
        user.is_active = True
        user.save()

        return Response({"message": "Email verified successfully"}, status=status.HTTP_200_OK)


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

        # ❌ Login Errors
        errors = serializer.errors

        # 📧 Resend verification email if not verified
        if "email_not_verified" in errors:
            try:
                user = CustomUser.objects.get(
                    email=request.data.get("email")
                )

                # 🔐 Generate uid + token
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                token = default_token_generator.make_token(user)

                # 🔗 SAME verification link as signup
                verification_link = (
                    f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}/"
                )

                # 📧 SAME HTML email as signup
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
                email.send(fail_silently=False)

            except CustomUser.DoesNotExist:
                pass

        return Response(errors, status=400)

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # 🔥 Delete current user's token
        request.user.auth_token.delete()

        return Response({
            "message": "Logged out successfully"
        }, status=200)


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=400)

        # 🔐 Generate uid + token
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        # 🔗 Frontend reset link
        reset_link = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"

        # 📧 HTML email
        html_content = render_to_string(
            'email/reset_password.html',
            {
                'user': user,
                'reset_link': reset_link
            }
        )

        email_msg = EmailMultiAlternatives(
            subject="Reset Your Password - NotesSnipt",
            body="Reset your password",
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email],
        )

        email_msg.attach_alternative(html_content, "text/html")
        email_msg.send()

        return Response({"message": "Reset link sent to your email"})

class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, uid, token):
        serializer = ResetPasswordSerializer(data=request.data)

        if serializer.is_valid():
            try:
                user_id = force_str(urlsafe_base64_decode(uid))
                user = CustomUser.objects.get(pk=user_id)
            except:
                return Response({"error": "Invalid user"}, status=400)

            if not default_token_generator.check_token(user, token):
                return Response({"error": "Invalid or expired link"}, status=400)

            user.set_password(serializer.validated_data['password'])
            user.save()

            return Response({"message": "Password reset successful"})

        return Response(serializer.errors, status=400)


#Admin
class AdminLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminLoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data

            # 🔐 Token create / get
            token, _ = Token.objects.get_or_create(user=user)

            return Response(
                {
                    "message": "Admin login successful",
                    "token": token.key,
                    "email": user.email,
                    "full_name": user.full_name,
                    "is_admin": user.is_admin
                },
                status=status.HTTP_200_OK
            )
        print("ADMIN LOGIN ERROR:", serializer.errors)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    
class AdminUpdateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def put(self, request, user_id):

        try:
            user = CustomUser.objects.get(id=user_id)

        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=404
            )

        # 🔥 Prevent updating admin users
        if user.is_admin:
            return Response(
                {"error": "Admin users cannot be updated."},
                status=403
            )

        serializer = AdminUserUpdateSerializer(
            user,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response({
                "message": "User updated successfully"
            })

        return Response(
            serializer.errors,
            status=400
        )
    
    
class AdminDeleteUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def delete(self, request, user_id):

        try:
            user = CustomUser.objects.get(id=user_id)

        except CustomUser.DoesNotExist:
            return Response(
                {"error": "User not found"},
                status=404
            )

        # 🔥 Prevent deleting admin users
        if user.is_admin:
            return Response(
                {"error": "Admin users cannot be deleted."},
                status=403
            )

        user.delete()

        return Response({
            "message": "User deleted successfully"
        })
    
class AdminPagination(PageNumberPagination):
    page_size = 20

class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def get(self, request):
        # users = CustomUser.objects.prefetch_related('notes').all().order_by('-id')
        users = CustomUser._base_manager.prefetch_related('notes').all().order_by('-id')
        # print("ALL USERS:", users)
        # 🔍 search
        search = request.GET.get('search')
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(full_name__icontains=search)
            )

        paginator = AdminPagination()
        result_page = paginator.paginate_queryset(users, request)
        # print("PAGINATED USERS:", result_page)
        serializer = AdminUserSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)



class AdminLogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        # 🔥 Delete current user's token
        request.user.auth_token.delete()

        return Response({
            "message": "Logged out successfully"
        }, status=200)