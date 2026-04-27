from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework.authtoken.models import Token
from accounts.models import CustomUser
from accounts.serializers import SignupSerializer, LoginSerializer, ResetPasswordSerializer, AdminLoginSerializer, AdminUserSerializer, AdminUserSerializer, AdminUserUpdateSerializer, AdminNoteUpdateSerializer
from accounts.utils import email_verification_token
from django.utils import timezone
from django.urls import reverse
from django.core.mail import send_mail
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

# class AdminSignupView(APIView):
#     permission_classes = [IsAuthenticated]

#     def post(self, request):
#         if not request.user.is_admin:
#             return Response({"error": "Only admin can create another admin"}, status=403)
#         serializer = AdminSignupSerializer(data=request.data)
#         if serializer.is_valid():
#             serializer.save()
#             return Response({"message": "Admin user created"}, status=201)
#         return Response(serializer.errors, status=400)

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


class AdminPagination(PageNumberPagination):
    page_size = 5

class AdminUserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def get(self, request):
        users = CustomUser.objects.prefetch_related('notes').all()

        # 🔍 search
        search = request.GET.get('search')
        if search:
            users = users.filter(
                Q(email__icontains=search) |
                Q(full_name__icontains=search)
            )

        paginator = AdminPagination()
        result_page = paginator.paginate_queryset(users, request)

        serializer = AdminUserSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)
    
class AdminUpdateUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def put(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        serializer = AdminUserUpdateSerializer(user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User updated successfully"})

        return Response(serializer.errors, status=400)
    
    
class AdminDeleteUserView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def delete(self, request, user_id):
        try:
            user = CustomUser.objects.get(id=user_id)
        except CustomUser.DoesNotExist:
            return Response({"error": "User not found"}, status=404)

        user.delete()
        return Response({"message": "User deleted successfully"})
    
class AdminUpdateNoteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def put(self, request, note_id):
        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=404)

        serializer = AdminNoteUpdateSerializer(note, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Note updated successfully"})

        return Response(serializer.errors, status=400)
    

class AdminDeleteNoteView(APIView):
    permission_classes = [IsAuthenticated, IsAdminOnly]

    def delete(self, request, note_id):
        try:
            note = Note.objects.get(id=note_id)
        except Note.DoesNotExist:
            return Response({"error": "Note not found"}, status=404)

        note.delete()   # 🔥 HARD DELETE

        return Response({"message": "Note permanently deleted"})