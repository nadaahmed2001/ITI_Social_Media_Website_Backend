from .models import User
from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Profile, Skill
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from .serializers import UserSerializer, RegisterStudentSerializer, LoginSerializer, ProfileSerializer, SkillSerializer, PasswordResetSerializer, SetNewPasswordSerializer
from batches.models import StudentBatch, VerifiedNationalID, UnverifiedNationalID, Student
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail
from django.utils.crypto import get_random_string
import secrets
from datetime import timedelta
from django.utils import timezone


@method_decorator(csrf_exempt, name="dispatch")
class RegisterStudentView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        print("I am in the register student view")
        serializer = RegisterStudentSerializer(data=request.data)
        if serializer.is_valid():
            national_id = serializer.validated_data["national_id"]

            try:
                unverified_entry = UnverifiedNationalID.objects.get(national_id=national_id)
                print("I have found the unverified entry: ", unverified_entry)

                if VerifiedNationalID.objects.filter(national_id=national_id).exists():
                    return Response({"error": "This National ID is already registered"}, status=status.HTTP_400_BAD_REQUEST)

                batch = unverified_entry.batch
                user = serializer.save()
                user.is_student = True
                user.is_active = True
                user.save()
                print("I have created the user: ", user)

                student = Student.objects.create(user=user, status="Active")
                print("I have created the student: ", student)
                StudentBatch.objects.create(student=student, batch=batch)
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

# ===============================================================================================================================================
class PasswordResetRequestView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data["email"]
            user = get_object_or_404(User, email=email)

            reset_code = user.generate_reset_code()  

            user.password_reset_code = reset_code
            user.reset_code_expiry = timezone.now() + timedelta(hours=1)
            user.save()

            send_mail(
                "Password Reset Code",
                f"Your password reset code is: {reset_code}. Please use this code to reset your password.",
                "noreply@itihub.com",
                [user.email],
                fail_silently=False,
            )

            return Response({"message": "Password reset code sent successfully."}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PasswordResetConfirmView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        reset_code = request.data.get("reset_code")
        new_password = request.data.get("new_password")

        if not reset_code or not new_password:
            return Response({"error": "Reset code and new password are required."}, status=status.HTTP_400_BAD_REQUEST)

        user = User.objects.filter(password_reset_code=reset_code).first()
        if user is None:
            return Response({"error": "Invalid or expired reset code."}, status=status.HTTP_400_BAD_REQUEST)

        if user.is_reset_code_expired():
            return Response({"error": "The reset code has expired."}, status=status.HTTP_400_BAD_REQUEST)

    
        user.set_password(new_password)
        user.password_reset_code = ""  
        user.reset_code_expiry = None  
        user.save()

        return Response({"message": "Password reset successfully."}, status=status.HTTP_200_OK)



# ===============================================================================================================================================
# ======================================================= Profile & Skills Views ================================================================
class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow owners of the profile to edit it, while others can only view it.
    """
    def has_object_permission(self, request, view, obj):
        # Check if the user is the owner of the profile or is making a read-only request
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.user == request.user

class UserAccountAPI(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    def get(self, request):
        # Get the logged-in user's profile
        profile = request.user.profile
        serializer = ProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request):
        # Get the logged-in user's profile
        profile = request.user.profile
        serializer = ProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# ==============================================================================================================================================
class AllProfilesAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        """
        Get all profiles and their associated skills.
        """
        profiles = Profile.objects.all()  # Retrieve all profiles
        all_profiles_data = []

        # Loop through each profile and serialize the data
        for profile in profiles:
            profile_data = ProfileSerializer(profile).data  # Serialize individual profile
            
            # Fetching skills for each profile
            main_skills = profile.skill_set.exclude(description__exact="")  # Main skills with description
            other_skills = profile.skill_set.filter(description="")  # Skills without description
            
            # Add skills to the profile data
            profile_data["main_skills"] = SkillSerializer(main_skills, many=True).data
            profile_data["other_skills"] = SkillSerializer(other_skills, many=True).data
            
            # Add the profile data to the list
            all_profiles_data.append(profile_data)

        return Response(all_profiles_data, status=status.HTTP_200_OK)

class UserProfileAPI(APIView):
    def get(self, request, id):
        """
        Get a specific profile and its associated skills.
        """
        profile = get_object_or_404(Profile, id=id)  # Retrieve the specific profile by ID
        
        # Categorizing skills
        main_skills = profile.skill_set.exclude(description__exact="")
        other_skills = profile.skill_set.filter(description="")
        
        # Serializing the profile data
        profile_data = ProfileSerializer(profile).data
        profile_data["main_skills"] = SkillSerializer(main_skills, many=True).data
        profile_data["other_skills"] = SkillSerializer(other_skills, many=True).data

        return Response(profile_data, status=status.HTTP_200_OK)

# ===============================================================================================================================================
class SkillAPI(APIView):
    permission_classes = [IsAuthenticated]
    
    # Disable CSRF for the entire class-based view
    @csrf_exempt
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, pk=None):
        profile = request.user.profile
        
        if pk:
            # Retrieve a specific skill by pk
            skill = get_object_or_404(Skill, pk=pk, owner=profile)
            serializer = SkillSerializer(skill)
            return Response(serializer.data)
        
        # Retrieve all skills for the logged-in user's profile
        skills = Skill.objects.filter(owner=profile)
        serializer = SkillSerializer(skills, many=True)
        return Response(serializer.data)

    def post(self, request):
        # Check if the skill name already exists
        skill_name = request.data.get('name').strip()
        # Case-insensitive check for existing skill name
        if Skill.objects.filter(name__iexact=skill_name).exists():
            return Response({"detail": "A skill with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)

        # Add a new skill to the logged-in user's profile
        profile = request.user.profile
        
        # Deserialize the data to create a new skill
        serializer = SkillSerializer(data=request.data)
        
        if serializer.is_valid():
            # Associate the skill with the logged-in user's profile
            serializer.save(owner=profile)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

    def put(self, request, pk):
        # Get the skill object that belongs to the logged-in user's profile
        profile = request.user.profile
        skill = get_object_or_404(Skill, pk=pk, owner=profile)
        
        # Get the new skill name from the request data
        skill_name = request.data.get('name').strip()

        # Check if another skill with the same name (case-insensitive) already exists (excluding the current skill)
        if Skill.objects.filter(name__iexact=skill_name).exclude(pk=pk).exists():
            return Response({"detail": "A skill with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)
        
        # Deserialize the data to update the skill
        serializer = SkillSerializer(skill, data=request.data, partial=True)  # Partial update
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        # Get the skill object that belongs to the logged-in user's profile
        profile = request.user.profile
        skill = get_object_or_404(Skill, pk=pk, owner=profile)
        
        # Delete the skill
        skill.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

