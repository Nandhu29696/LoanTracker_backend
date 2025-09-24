# accounts/admin.py
from django.contrib import admin
from .models import EmailOTP

@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = ("user", "otp", "purpose", "used", "created_at", "expires_at")
    search_fields = ("user__email", "otp")
