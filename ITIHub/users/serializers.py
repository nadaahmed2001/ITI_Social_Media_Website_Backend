from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User
from batches.models import StudentBatch
from users.models import Profile, Skill
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth import get_user_model, password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer as BaseTokenObtainPairSerializer
from rest_framework.exceptions import APIException
from django.core.mail import EmailMultiAlternatives
from rest_framework import status
from django.utils import timezone
from .models import UserOTP


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email", "phone", "is_student", "is_supervisor"]

class RegisterStudentSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "national_id"]

    def create(self, validated_data):
        validated_data["is_student"] = True
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

class ProfileSerializer(serializers.ModelSerializer):
    profile_picture = serializers.URLField(max_length=500, required=False, allow_null=True)
    is_two_factor_enabled = serializers.BooleanField(source='user.is_two_factor_enabled', required=False)

    class Meta:
        model = Profile
        fields = "__all__"
        read_only_fields = ['user', 'created', 'updated']

    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', None)
        if user_data is not None:
            user = instance.user
            user.is_two_factor_enabled = user_data.get('is_two_factor_enabled', user.is_two_factor_enabled)
            user.save(update_fields=['is_two_factor_enabled'])

        instance = super().update(instance, validated_data)
        return instance


class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = '__all__'
        

#reset password serializers
class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField()

class SetNewPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data

User = get_user_model()

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    confirm_new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is not correct.")
        return value

    def validate_new_password(self, value):
        try:
            password_validation.validate_password(value, self.context['request'].user)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def validate(self, data):
        if data['new_password'] != data['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "New passwords must match."})
        
        if data['new_password'] == data['current_password']:
            raise serializers.ValidationError({"new_password": "New password cannot be the same as the current password."})
        
        return data

class ChangeEmailSerializer(serializers.Serializer):
    new_email = serializers.EmailField(required=True)
    confirm_new_email = serializers.EmailField(required=True, write_only=True)
    current_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is not correct for authorization.")
        return value

    def validate_new_email(self, value):
        user = self.context['request'].user
        new_email = value.lower().strip()

        if new_email == user.email.lower():
            raise serializers.ValidationError("New email cannot be the same as the current email.")

        if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError("This email address is already in use by another account.")
        return new_email

    def validate(self, data):
        if data['new_email'].lower() != data['confirm_new_email'].lower():
            raise serializers.ValidationError({"confirm_new_email": "New email addresses must match."})
        return data
    
from .models import UserOTP

# users/serializers.py


# Keep other serializers: UserSerializer, RegisterStudentSerializer, ProfileSerializer, etc.
# ...

User = get_user_model()

class CustomTokenObtainPairSerializer(BaseTokenObtainPairSerializer):
    """
    Customizes the JWT token obtaining process to include 2FA via email OTP.
    """

    # Custom Exception to signal frontend that OTP is required
    class OTPAuthenticationFailed(APIException):
        status_code = status.HTTP_200_OK # Return 200 OK because credentials *were* valid
        default_detail = 'OTP Required.'
        default_code = 'otp_required'

        def __init__(self, detail=None, code=None):
            # Structure the response detail for the frontend
            self.detail = {
                'detail': detail or self.default_detail,
                'code': code or self.default_code,
                'otp_required': True,
                'message': 'OTP sent to your registered email.' # Informative message
            }

    @classmethod
    def get_token(cls, user):
        # Standard method to generate JWT token pair
        token = super().get_token(user)
        # Optional: Add custom claims to the token payload here if needed
        # token['username'] = user.username
        return token

    def validate(self, attrs):
        # --- Step 1: Validate Username/Password ---
        # Call the parent's validate method first. It checks credentials
        # and sets `self.user` if they are valid. It raises AuthenticationFailed
        # if credentials are invalid, which we let propagate.
        try:
            # Note: super().validate() returns token data if successful by default,
            # but we don't use that return value directly here yet.
            super().validate(attrs)
        except Exception as e:
            # Log credential failure for debugging if needed
            # print(f"Credential validation failed during super().validate: {e}")
            raise # Re-raise the original AuthenticationFailed or other validation error

        # --- Safety check (should have self.user if super().validate passed) ---
        if not hasattr(self, 'user') or not self.user:
             # This should ideally not happen if super().validate didn't raise error
             raise serializers.ValidationError("User authentication failed unexpectedly.", code='authorization')

        # --- Step 2: Check if 2FA is Enabled ---
        if self.user.is_two_factor_enabled:
            print(f"DEBUG: 2FA is TRUE for {self.user.username}, attempting OTP process...")
            otp_generated_and_sent = False # Flag to track success within try block

            try:
                # --- Step 3a: Clear old OTPs and Create New ---
                UserOTP.objects.filter(user=self.user).delete()
                otp_instance = UserOTP.objects.create(user=self.user) # save() generates code/expiry
                otp_code = otp_instance.otp_code
                expiration_minutes = getattr(settings, 'OTP_EXPIRATION_MINUTES', 10)
                current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')

                # --- Step 3b: Prepare and Send Email ---
                subject = f"Your Login Verification Code for {settings.SITE_NAME or 'ITIHub'}"
                sender = settings.DEFAULT_FROM_EMAIL
                recipient = self.user.email

                if not recipient:
                    # If email is mandatory for 2FA, treat this as a configuration error
                    print(f"Cannot send OTP to {self.user.username}: No email configured.")
                    raise serializers.ValidationError("Cannot perform 2FA: No email address found for user.", code='authorization')

                # Use the HTML email template you provided
                html_message = f"""
                <!DOCTYPE html>
                <html>
                <head> <meta charset="UTF-8"> <title>{subject}</title> <style> /* Your Email CSS Styles Here */ body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; line-height: 1.6; color: #333333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9f9f9; }} .email-container {{ background-color: #ffffff; border-radius: 8px; box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1); overflow: hidden; }} .header {{ padding: 25px; text-align: center; background-color: #f0f4f8; border-bottom: 1px solid #e0e6ed; }} .logo {{ max-height: 50px; margin-bottom: 15px; }} .content {{ padding: 25px; }} .otp-code {{ font-size: 32px; letter-spacing: 5px; text-align: center; margin: 25px 0; padding: 15px; background-color: #f8fafc; border: 1px dashed #e2e8f0; border-radius: 6px; color: #1e40af; font-weight: bold; }} .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #64748b; background-color: #f0f4f8; border-top: 1px solid #e0e6ed; }} .info-box {{ background-color: #f8fafc; border-left: 4px solid #4f46e5; padding: 15px; margin: 20px 0; border-radius: 0 4px 4px 0; }} .divider {{ height: 1px; background-color: #e2e8f0; margin: 20px 0; }} </style> </head>
                <body> <div class="email-container"> <div class="header"> <img src="{settings.LOGO_URL or 'https://via.placeholder.com/150x50'}" alt="{settings.SITE_NAME or 'App'}" class="logo"> <h2 style="margin: 10px 0 0; color: #1e293b;">Login Verification</h2> </div> <div class="content"> <p>Hello <strong>{self.user.username}</strong>,</p> <p>We received a login attempt for your {settings.SITE_NAME or 'account'} on {current_time}.</p> <div class="info-box"> <p style="margin: 0;">For security reasons, please verify this login attempt using the following One-Time Password:</p> </div> <div class="otp-code">{otp_code}</div> <p>This code will expire in <strong>{expiration_minutes} minutes</strong>.</p> <div class="divider"></div> <p><strong>Security Tips:</strong></p> <ul> <li>Never share this code with anyone</li> <li>This code can only be used once</li> <li>If you didn't request this, please secure your account immediately</li> </ul> </div> <div class="footer"> <p>&copy; {timezone.now().year} {settings.SITE_NAME or 'Our App'}. All rights reserved.</p> <p>This email was sent to {recipient} for account security purposes.</p> </div> </div> </body>
                </html>
                """

                # Plain text version (keep for compatibility)
                plain_message = f"""Login Verification for {settings.SITE_NAME or 'ITIHub'}... Your One-Time Password is: {otp_code} ...""" # Keep your full plain text version

                # Send email
                msg = EmailMultiAlternatives(subject, plain_message, sender, [recipient])
                msg.attach_alternative(html_message, "text/html")
                msg.send() # Use fail_silently=False by default

                # If email sending succeeded, mark flag
                otp_generated_and_sent = True
                print(f"DEBUG: OTP email supposedly sent to {recipient}.")

            except Exception as e:
                # Catch ONLY errors from the OTP/Email process inside the try block
                print(f"Error during OTP generation/sending for {self.user.username}: {e}")
                # Raise the generic validation error only if this specific process fails
                raise serializers.ValidationError("Could not process two-factor authentication request.", code='authorization')

            # --- Step 4: Raise Custom Exception AFTER successful OTP process ---
            # If the try block completed without errors, raise the exception to signal frontend
            if otp_generated_and_sent:
                print(f"DEBUG: OTP process successful for {self.user.username}. Raising OTPAuthenticationFailed.")
                raise self.OTPAuthenticationFailed()
            else:
                # This case should theoretically not be reached if fail_silently=False
                # unless the 'recipient' check failed and raised ValidationError earlier.
                # But as a fallback:
                 raise serializers.ValidationError("Failed to send OTP.", code='authorization')

        else:
            # --- Step 5: 2FA Disabled - Return Tokens ---
            print(f"DEBUG: 2FA is FALSE for {self.user.username}, generating tokens...")
            refresh = self.get_token(self.user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                # Optionally include user details if your frontend needs them on login
                # 'user': UserSerializer(self.user).data
            }
            return data # Return token data directly

class VerifyOTPSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    otp_code = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate(self, data):
        username = data.get('username')
        otp_code = data.get('otp_code')
        user = None

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        otp_instance = UserOTP.objects.filter(user=user).order_by('-created_at').first()

        if not otp_instance:
            raise serializers.ValidationError("No active OTP found for this user. Please log in again.")

        if otp_instance.is_expired():
            otp_instance.delete()
            raise serializers.ValidationError("OTP has expired. Please log in again.")

        if otp_instance.otp_code != otp_code:
            raise serializers.ValidationError("Invalid OTP code.")

        print(f"Verified OTP for {user.username}.")
        data['user'] = user
        data['otp_instance'] = otp_instance
        return data