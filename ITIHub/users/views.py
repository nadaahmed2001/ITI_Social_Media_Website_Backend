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
                            ChangeEmailSerializer,
                            VerifyOTPSerializer)
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
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
from .models import Skill
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import EmailMultiAlternatives
from rest_framework_simplejwt.views import TokenObtainPairView as BaseTokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer




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
    permission_classes = [IsAuthenticated]
    # --- Add Parsers to handle potential file uploads ---
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        try:
            # Get the profile associated with the logged-in user
            profile = request.user.profile
            # Serialize the profile data
            serializer = ProfileSerializer(profile, context={'request': request}) # Pass context if needed by serializer
            return Response(serializer.data, status=status.HTTP_200_OK)
        except ObjectDoesNotExist:
            # Handle case where user exists but profile doesn't (shouldn't happen with signals)
            return Response({"detail": "Profile not found for this user."}, status=status.HTTP_404_NOT_FOUND)
        except AttributeError:
            # Handle case where request.user doesn't have .profile (less likely for OneToOne)
            return Response({"detail": "Error accessing profile."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request):
        try:
            profile = request.user.profile
        except ObjectDoesNotExist:
            return Response({"detail": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
        # The ProfileSerializer's update method now handles saving the
        # 'is_two_factor_enabled' field to the related User model.
        serializer = ProfileSerializer(profile, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save() # Serializer's update handles user field
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
            subject = f"Password Changed for Your {settings.SITE_NAME} account"
            change_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')
            reset_password_url = f"{settings.BACKEND_BASE_URL.rstrip('/')}/users/password-reset/"
            support_email = settings.DEFAULT_FROM_EMAIL or 'support@example.com'
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{subject}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        text-align: center;
                        padding-bottom: 20px;
                        border-bottom: 1px solid #eee;
                        margin-bottom: 20px;
                    }}
                    .logo {{
                        max-width: 150px;
                        margin-bottom: 15px;
                    }}
                    .content {{
                        padding: 20px 0;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 5px 20px;
                        background-color: #4CAF50;
                        color: white !important;
                        text-decoration: none;
                        border-radius: 4px;
                        margin: 10px 0px 5px 5px;
                    }}
                    .footer {{
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                        font-size: 12px;
                        color: #777;
                        text-align: center;
                    }}
                    .alert {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-left: 4px solid #dc3545;
                        margin: 20px 0;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <img src="{settings.LOGO_URL}" alt="{settings.SITE_NAME or 'ITIHub'}" class="logo">
                    <h2>Password Changed Successfully</h2>
                </div>
                
                <div class="content">
                    <p>Hello {user.username},</p>
                    
                    <p>This is a confirmation that the password for your {settings.SITE_NAME or 'account'} was successfully changed on <strong>{change_time}</strong>.</p>
                    
                    <div class="alert">
                        <p><strong>Important Security Information:</strong></p>
                        <p>If you did <strong>not</strong> initiate this password change, your account security may be compromised.</p>
                    </div>
                    
                    <p>If this wasn't you, please take immediate action:</p>
                    <ol>
                        <li><a href="{reset_password_url}" class="button">Reset Your Password Now</a></li>
                        <li> Contact our support team at <a href="mailto:{support_email}">{support_email}</a></li>
                        <li> Check your account for any unauthorized activity</li>
                    </ol>
                    
                    <p>If you did make this change, you can safely ignore this email.</p>
                </div>
                
                <div class="footer">
                    <p>&copy; {timezone.now().year} {settings.SITE_NAME or 'ITIHub'}. All rights reserved.</p>
                    <p>This email was sent to {user.email} because a password change was detected on your account.</p>
                </div>
            </body>
            </html>
            """
            
            plain_message = (
                f"Hi {user.username},\n\n"
                f"This is a confirmation that the password for your {settings.SITE_NAME } account was successfully changed at {change_time}.\n\n"
                f"If you made this change, you can safely ignore this email.\n\n"
                f"IF YOU DID NOT CHANGE YOUR PASSWORD:\n"
                f"1. Reset your password immediately: {reset_password_url}\n"
                f"2. Contact our support team at {support_email}\n"
                f"3. Check your account for any unauthorized activity\n\n"
                f"Thanks,\n{settings.SITE_NAME or 'ITIHub'} Team"
            )

            sender = settings.DEFAULT_FROM_EMAIL 
            recipient = user.email

            send_mail(
                subject=subject,
                message=plain_message,
                html_message=html_message,
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
        serializer.is_valid(raise_exception=True)

        user = request.user
        new_email = serializer.validated_data['new_email']

        try:
            # Delete any previous pending requests for this user
            EmailChangeRequest.objects.filter(user=user).delete()

            # Create a new request object
            change_request = EmailChangeRequest.objects.create(user=user, new_email=new_email)
            token = change_request.token

            # Construct Confirmation URL
            relative_url = reverse('confirm-email-change', kwargs={'token': token})
            confirmation_url = f"{settings.BACKEND_BASE_URL.rstrip('/')}{relative_url}"
            
            # Email content
            subject = f"Confirm Your Email Change for {settings.SITE_NAME or 'Your Account'}"
            expiration_hours = settings.EMAIL_CHANGE_EXPIRATION_HOURS or 1
            support_email = settings.SUPPORT_EMAIL or 'support@example.com'
            
            html_message = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>{subject}</title>
                <style>
                    body {{
                        font-family: Arial, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                    }}
                    .header {{
                        text-align: center;
                        padding-bottom: 20px;
                        border-bottom: 1px solid #eee;
                        margin-bottom: 20px;
                    }}
                    .logo {{
                        max-width: 150px;
                        margin-bottom: 15px;
                    }}
                    .content {{
                        padding: 20px 0;
                    }}
                    .button {{
                        display: inline-block;
                        padding: 12px 24px;
                        background-color: #2563eb;
                        color: white !important;
                        text-decoration: none;
                        border-radius: 4px;
                        margin: 20px 0;
                        font-weight: bold;
                    }}
                    .footer {{
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #eee;
                        font-size: 12px;
                        color: #777;
                        text-align: center;
                    }}
                    .alert {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-left: 4px solid #dc3545;
                        margin: 20px 0;
                    }}
                    .code {{
                        font-family: monospace;
                        background-color: #f3f4f6;
                        padding: 10px;
                        border-radius: 4px;
                        word-break: break-all;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <img src="{settings.LOGO_URL or 'https://via.placeholder.com/150'}" alt="{settings.SITE_NAME or 'ITIHub'}" class="logo">
                    <h2>Confirm Your Email Change</h2>
                </div>
                
                <div class="content">
                    <p>Hello {user.username},</p>
                    
                    <p>We received a request to change the email address associated with your {settings.SITE_NAME or 'account'} from <strong>{user.email}</strong> to <strong>{new_email}</strong>.</p>
                    
                    <p style="text-align: center;">
                        <a href="{confirmation_url}" class="button">Confirm Email Change</a>
                    </p>
                    
                    <p>This link will expire in <strong>{expiration_hours} hour(s)</strong>.</p>
                    
                    <div class="alert">
                        <p><strong>Important:</strong> If you didn't request this change, please:</p>
                        <ol>
                            <li>Secure your account by changing your password immediately</li>
                            <li>Contact our support team at <a href="mailto:{support_email}">{support_email}</a></li>
                        </ol>
                    </div>
                    
                    <p>Alternatively, you can copy and paste this URL into your browser:</p>
                    <div class="code">{confirmation_url}</div>
                </div>
                
                <div class="footer">
                    <p>&copy; {timezone.now().year} {settings.SITE_NAME or 'ITIHub'}. All rights reserved.</p>
                    <p>This email was sent to {new_email} because an email change was requested for your account.</p>
                </div>
            </body>
            </html>
            """
            
            plain_message = (
                f"Hi {user.username},\n\n"
                f"We received a request to change the email address associated with your {settings.SITE_NAME or 'account'} from {user.email} to {new_email}.\n\n"
                f"Please click the following link to confirm this change:\n\n"
                f"{confirmation_url}\n\n"
                f"This link will expire in {expiration_hours} hour(s).\n\n"
                f"IMPORTANT: If you didn't request this change, please:\n"
                f"1. Secure your account by changing your password immediately\n"
                f"2. Contact our support team at {support_email}\n\n"
                f"Thanks,\n{settings.SITE_NAME or 'ITIHub'} Team"
            )

            # Send email
            msg = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[new_email]
            )
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


class VerifyOTPView(APIView):
    """
    Verifies the OTP submitted after initial login for 2FA enabled users.
    Expects 'username' and 'otp_code'. Issues JWT tokens on success.
    """
    permission_classes = [AllowAny] # Allow access before full authentication
    serializer_class = VerifyOTPSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        # is_valid runs the validate method in the serializer
        serializer.is_valid(raise_exception=True)

        # If validation passed, serializer includes 'user' and 'otp_instance'
        user = serializer.validated_data['user']
        otp_instance = serializer.validated_data['otp_instance']

        # Clean up the used OTP
        otp_instance.delete()

        # Generate JWT tokens for the verified user
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)

        # Optional: Add user details to response
        user_serializer = UserSerializer(user) # Assuming you have a UserSerializer

        return Response({
            'refresh': str(refresh),
            'access': access_token,
            'user': user_serializer.data # Optional: send user details back
        }, status=status.HTTP_200_OK)



class CustomTokenObtainPairView(BaseTokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer