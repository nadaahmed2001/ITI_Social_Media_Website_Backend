from django.contrib.auth import authenticate
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from .models import Profile, EmailChangeRequest
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.csrf import csrf_exempt
from .serializers import (  UserSerializer, 
                            RegisterStudentSerializer, 
                            LoginSerializer, 
                            ProfileSerializer, 
                            SkillSerializer, 
                            ChangePasswordSerializer, 
                            ChangeEmailSerializer)

from batches.models import StudentBatch, VerifiedNationalID, UnverifiedNationalID, Student
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.db import transaction 
from .serializers import ChangePasswordSerializer, ChangeEmailSerializer
from .models import Profile
from django.urls import reverse
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone



class RegisterStudentView(APIView):
    def post(self, request):
        print("I am in the register student view")
        serializer = RegisterStudentSerializer(data=request.data)
        if serializer.is_valid():
            national_id = serializer.validated_data["national_id"]

            try:
                unverified_entry = UnverifiedNationalID.objects.get(national_id=national_id)
                print("I have found the unverified entry: ", unverified_entry)

                # Ensure the student hasn't already registered
                if VerifiedNationalID.objects.filter(national_id=national_id).exists():
                    return Response({"error": "This National ID is already registered"}, status=status.HTTP_400_BAD_REQUEST)

                batch = unverified_entry.batch
                user = serializer.save()
                user.is_student = True
                user.is_active = True
                user.save()
                print("I have created the user: ", user)

                # Create a student 
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

    @csrf_exempt
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


# ========================================= User account change email - change password views ===================================================
User = get_user_model()

class ChangePasswordView(APIView):
    """
    Endpoint for changing the user's password.
    Requires current_password, new_password, confirm_new_password.
    Sends a notification email upon successful change.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangePasswordSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_password = serializer.validated_data['new_password']

        # Set and save the new password
        user.set_password(new_password)
        user.save()

        # --- Send Password Change Notification Email ---
        try:
            subject = f"Password Changed for Your Account on {settings.SITE_NAME or 'ITIHub'}" # Use SITE_NAME from settings if defined
            # Add a timestamp for context
            change_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z') # e.g., 2025-04-03 04:21:27 EET
            reset_password_url = f"{settings.BACKEND_BASE_URL.rstrip('/')}/users/password-reset/"
            message = (
                f"Hi {user.username},\n\n"
                f"This is a confirmation that the password for your account was successfully changed at {change_time}.\n\n"
                f"If you made this change, Ignore this email.\n\n"
                f"If you did NOT change your password, please secure your account immediately by resetting your password "
                f"and contact our support team.\n\n"
                f"Reset Password: ({reset_password_url}) \n\n"
                f"Thanks,\n{settings.SITE_NAME or 'ITIHub'}" # Customize signature
            )
            sender = settings.DEFAULT_FROM_EMAIL 
            recipient = user.email

            send_mail(
                subject=subject,
                message=message,
                from_email=sender,
                recipient_list=[recipient],
                fail_silently=False 
            )
            

        except Exception as e:
            print(f"ERROR: Failed to send password change notification email to {user.email}: {e}")
        
        return Response({"message": "Password updated successfully."}, status=status.HTTP_200_OK)

class ChangeEmailView(APIView):
    """
    Endpoint to initiate changing the user's email address.
    Requires new_email, confirm_new_email, current_password.
    Sends a confirmation email to the new address.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ChangeEmailSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        # This automatically checks: password correct, emails match, new email format, new email not used by OTHERS
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_email = serializer.validated_data['new_email']

        # --- Email Verification Flow ---
        try:
            # 1. Delete any previous pending requests for this user
            EmailChangeRequest.objects.filter(user=user).delete()

            # 2. Create a new request object (token and expiration set on save)
            change_request = EmailChangeRequest.objects.create(user=user, new_email=new_email)
            token = change_request.token

            # 3. Construct Confirmation URL (using API endpoint)
            # Uses reverse() to get the URL based on the URL pattern name
            relative_url = reverse('confirm-email-change', kwargs={'token': token})
            # Ensure settings.BACKEND_BASE_URL ends WITHOUT a slash and relative_url STARTS with one
            confirmation_url = f"{settings.BACKEND_BASE_URL.rstrip('/')}{relative_url}" 

            # --- Modify email message ---
            subject = "Confirm Your Email Change"
            link_tag = f'<a href="{confirmation_url}" target="_blank" rel="noopener noreferrer">Confirm Email Change</a>'
            message = (
                f"Hi {user.username},\n\n"
                f"Please click the link below to confirm changing your email address to {new_email}.\n\n"
                # Use the link_tag here for a clickable link
                f"{link_tag}\n\n"
                f"Or copy and paste this URL into your browser:\n{confirmation_url}\n\n"
                f"This link will expire in {settings.EMAIL_CHANGE_EXPIRATION_HOURS or 1} hour(s).\n\n"
                f"If you did not request this change, please ignore this email.\n\n"
                f"Thanks,\nYour Site Team"
            )
            sender = settings.DEFAULT_FROM_EMAIL

            # Consider sending HTML email for better link formatting
            from django.core.mail import EmailMultiAlternatives

            html_message = (
                f"<p>Hi {user.username},</p>"
                f"<p>Please click the link below to confirm changing your email address to {new_email}.</p>"
                f"<p>{link_tag}</p>"
                f"Or copy and paste this URL into your browser:\n{confirmation_url}\n\n"
                f"<p>This link will expire in {settings.EMAIL_CHANGE_EXPIRATION_HOURS or 1} hour(s).</p>"
                f"<p>If you did not request this change, please ignore this email.</p>"
                f"<p>Thanks,<br/>ITIHub Team</p>"
            )

            # Send both plain text and HTML
            msg = EmailMultiAlternatives(subject, message, sender, [new_email])
            msg.attach_alternative(html_message, "text/html")
            msg.send()

            return Response({
                "message": f"Confirmation email sent to {new_email}. Please click the link inside to complete the change."
            }, status=status.HTTP_200_OK)

        except Exception as e:
            print(f"Error initiating email change for {user.username}: {e}")
            return Response({"detail": "An error occurred while initiating the email change."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ConfirmEmailChangeView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, token, *args, **kwargs):
        try:
            change_request = get_object_or_404(EmailChangeRequest, token=token)

            if change_request.is_expired():
                change_request.delete()
                # Redirection to a frontend failure page
                failure_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/email-change-failed?reason=expired"
                return redirect(failure_url)
                
            with transaction.atomic():
                user_to_update = change_request.user
                new_email = change_request.new_email
                user_to_update.email = new_email
                user_to_update.save(update_fields=['email'])
                if hasattr(user_to_update, 'profile'):
                    user_to_update.profile.email = new_email
                    user_to_update.profile.save(update_fields=['email'])
                change_request.delete()

            # Redirect to Frontend Success Page 
            success_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/email-change-success" 
            return redirect(success_url)
            

        except EmailChangeRequest.DoesNotExist:
            failure_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/email-change-failed?reason=invalid"
            return redirect(failure_url)
        
        except Exception as e:
            print(f"Error confirming email change with token {token}: {e}")
            failure_url = f"{settings.FRONTEND_BASE_URL.rstrip('/')}/email-change-failed?reason=error"
            return redirect(failure_url)

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

