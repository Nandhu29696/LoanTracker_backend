# accounts/urls.py
from django.urls import path, include
from .views import (
    RegisterView, VerifyRegistrationOTPView,
    LoginRequestOTPView, VerifyLoginOTPView,
    AdminUserViewSet, RequestPasswordResetView, VerifyPasswordOTPView, ResetPasswordView

)
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenVerifyView

router = DefaultRouter()
router.register(r"admin/users", AdminUserViewSet, basename="admin-users")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("verify-otp/", VerifyRegistrationOTPView.as_view(), name="verify-otp"),
    path("login/request-otp/", LoginRequestOTPView.as_view(), name="login-request-otp"),
    path("login/verify-otp/", VerifyLoginOTPView.as_view(), name="login-verify-otp"),
    path("token/verify/", TokenVerifyView.as_view(), name="token_verify"),
    path("", include(router.urls)),

        # password reset
    path("password-reset/request/", RequestPasswordResetView.as_view(), name="password-reset-request"),
    path("password-reset/verify/", VerifyPasswordOTPView.as_view(), name="password-reset-verify"),
    path("password-reset/confirm/", ResetPasswordView.as_view(), name="password-reset-confirm"),

]
