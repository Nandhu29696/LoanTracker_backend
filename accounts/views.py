# accounts/views.py
from rest_framework import status, generics, viewsets
from rest_framework.response import Response
from django.contrib.auth import  get_user_model
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from .models import PasswordResetOTP
import random

from .serializers import RegisterSerializer, LoginSerializer, VerifyOTPSerializer, UserSerializer,     RequestPasswordResetSerializer, VerifyPasswordOTPSerializer, ResetPasswordSerializer
from .models import EmailOTP
from .utils import create_and_send_otp

User = get_user_model()

class RegisterView(generics.CreateAPIView):
    permission_classes = [AllowAny]
    serializer_class = RegisterSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        # send registration OTP to email
        create_and_send_otp(user, purpose="register")

    def create(self, request, *args, **kwargs):
        # return success telling user to verify email
        resp = super().create(request, *args, **kwargs)
        return Response({"detail": "Account created. Check email for OTP to verify your account."}, status=status.HTTP_201_CREATED)

class VerifyRegistrationOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp_text = serializer.validated_data["otp"]
        purpose = serializer.validated_data["purpose"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # find OTP
        try:
            otp = EmailOTP.objects.filter(user=user, otp=otp_text, purpose=purpose, used=False).latest("created_at")
        except EmailOTP.DoesNotExist:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({"detail": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

        otp.mark_used()
        if purpose == "register":
            user.is_active = True
            user.save()
            return Response({"detail": "Account verified. You can login now."})
        else:
            return Response({"detail": "OTP verified."})

class LoginRequestOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)

        # check password and active state
        if not user.check_password(password):
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({"detail": "Account not activated. Verify your email first."}, status=status.HTTP_403_FORBIDDEN)

        # generate and send OTP for login
        create_and_send_otp(user, purpose="login")
        return Response({"detail": "OTP sent to email. Use verify-login-otp endpoint to finish login."})

class VerifyLoginOTPView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    serializer_class = VerifyOTPSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]
        otp_text = serializer.validated_data["otp"]
        purpose = serializer.validated_data["purpose"]

        if purpose != "login":
            return Response({"detail": "Purpose must be 'login' for this endpoint."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # find OTP
        try:
            otp = EmailOTP.objects.filter(user=user, otp=otp_text, purpose=purpose, used=False).latest("created_at")
        except EmailOTP.DoesNotExist:
            return Response({"detail": "Invalid OTP."}, status=status.HTTP_400_BAD_REQUEST)

        if otp.is_expired():
            return Response({"detail": "OTP expired."}, status=status.HTTP_400_BAD_REQUEST)

        otp.mark_used()
        # issue tokens
        refresh = RefreshToken.for_user(user)
        return Response({
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "user": UserSerializer(user).data,
        })

# Admin user management viewset
class AdminUserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by("-date_joined")
    serializer_class = UserSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ["get","patch","put","delete","head","options"]

class RequestPasswordResetView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        serializer = RequestPasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            try:
                user = User.objects.get(email=email)
                otp = str(random.randint(100000, 999999))
                PasswordResetOTP.objects.create(user=user, otp=otp)

                create_and_send_otp(user, purpose="Password Reset")
                return Response({"message": "OTP sent to email","otp":otp}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User with this email does not exist"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class VerifyPasswordOTPView(APIView):
    def post(self, request):
        serializer = VerifyPasswordOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            otp = serializer.validated_data["otp"]
            try:
                user = User.objects.get(email=email)
                otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp).last()
                if otp_obj and otp_obj.is_valid():
                    return Response({"message": "OTP verified, proceed to reset password"}, status=status.HTTP_200_OK)
                return Response({"error": "Invalid or expired OTP"}, status=status.HTTP_400_BAD_REQUEST)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResetPasswordView(APIView):
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            new_password = serializer.validated_data["new_password"]
            try:
                user = User.objects.get(email=email)
                user.set_password(new_password)
                user.save()
                return Response({"message": "Password reset successful"}, status=status.HTTP_200_OK)
            except User.DoesNotExist:
                return Response({"error": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
