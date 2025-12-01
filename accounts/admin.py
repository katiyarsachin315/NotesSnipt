# accounts/admin.py
from django.contrib import admin
from accounts.models import CustomUser

class CustomUserAdmin(admin.ModelAdmin):
    model = CustomUser
    list_display = ['email', 'full_name', 'is_admin', 'is_active']
    search_fields = ['email', 'full_name']
    list_filter = ['is_active', 'is_admin']

admin.site.register(CustomUser, CustomUserAdmin)
