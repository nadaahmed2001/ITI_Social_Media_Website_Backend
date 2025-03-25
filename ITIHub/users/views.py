from django.contrib.auth import authenticate
from django.contrib.auth import login, logout
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.authtoken.models import Token
from .models import User
from .serializers import UserSerializer, RegisterStudentSerializer, LoginSerializer
from batches.models import StudentBatch, VerifiedNationalID, UnverifiedNationalID
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

class RegisterStudentView(APIView):
    def post(self, request):
        serializer = RegisterStudentSerializer(data=request.data)
        if serializer.is_valid():
            national_id = serializer.validated_data["national_id"]

            try:
                unverified_entry = UnverifiedNationalID.objects.get(national_id=national_id)
                batch = unverified_entry.batch

                if not batch:
                    return Response({"error": "No batch assigned to this National ID"}, status=status.HTTP_400_BAD_REQUEST)

                user = serializer.save()
                VerifiedNationalID.objects.create(national_id=national_id, batch=batch)
                StudentBatch.objects.create(student=user, batch=batch)
                unverified_entry.delete()

                return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
            except UnverifiedNationalID.DoesNotExist:
                return Response({"error": "This National ID is not allowed to register"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class LoginView(APIView):
    permission_classes = [AllowAny]  # Allow unauthenticated users to access this view

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = authenticate(
                username=serializer.validated_data["username"], 
                password=serializer.validated_data["password"]
            )
            if user:
                refresh = RefreshToken.for_user(user)
                return Response({
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                    "user": UserSerializer(user).data
                })
            return Response({"error": "Invalid Credentials"}, status=status.HTTP_400_BAD_REQUEST)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST)

            token = RefreshToken(refresh_token)
            token.blacklist()

            return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email
        })
