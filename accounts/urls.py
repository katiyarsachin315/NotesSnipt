from django.urls import path
from accounts.views import *

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('admin-login/', AdminLoginView.as_view(), name='admin-login'),
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('reset-password/<uid>/<token>/', ResetPasswordView.as_view(), name='reset-password'),
    path('verify-email/<uid>/<token>/', VerifyEmailView.as_view(), name='verify-email'),
    # ADMIN APIs
    path('admin/users/', AdminUserListView.as_view(), name='admin-users'),
    path('admin/user/<int:user_id>/', AdminUpdateUserView.as_view(), name='admin-update-user'),
    path('admin/user/<int:user_id>/delete/', AdminDeleteUserView.as_view(), name='admin-delete-user'),
    path('admin/note/<int:note_id>/', AdminUpdateNoteView.as_view(), name='admin-update-note'),
    path('admin/note/<int:note_id>/delete/', AdminDeleteNoteView.as_view(), name='admin-delete-note'),
]