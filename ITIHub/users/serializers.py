from rest_framework import serializers
from .models import User
from batches.models import StudentBatch
from users.models import Profile, Skill
from django.contrib.auth import get_user_model
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError as DjangoValidationError
from django.conf import settings
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.exceptions import APIException
from django.core.mail import send_mail
from rest_framework import status
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives


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

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):

    class OTPAuthenticationFailed(APIException):
        status_code = status.HTTP_200_OK
        default_detail = 'OTP Required.'
        default_code = 'otp_required'

        def __init__(self, detail=None, code=None):
            self.detail = {
                'detail': detail or self.default_detail,
                'code': code or self.default_code,
                'otp_required': True,
                'message': 'OTP sent to your registered email.'
            }

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        return token

    def validate(self, attrs):
        try:
            super().validate(attrs)
        except Exception as e:
            print(f"Credential validation failed: {e}")
            raise

        if not self.user:
            raise serializers.ValidationError("User validation failed unexpectedly.", code='authorization')

        if self.user.is_two_factor_enabled:
            print(f"DEBUG: 2FA enabled for {self.user.username}. OTP sent. Raising OTPAuthenticationFailed.")
            try:
                UserOTP.objects.filter(user=self.user).delete()
                otp_instance = UserOTP.objects.create(user=self.user)
                otp_code = otp_instance.otp_code
                expiration_minutes = getattr(settings, 'OTP_EXPIRATION_MINUTES', 10)
                current_time = timezone.now().strftime('%Y-%m-%d %H:%M:%S %Z')

                subject = f"Your Login Verification Code for {settings.SITE_NAME or 'ITIHub'}"
                sender = settings.DEFAULT_FROM_EMAIL
                recipient = self.user.email

                if not recipient:
                    print(f"Cannot send OTP to {self.user.username}: No email configured.")
                    raise serializers.ValidationError("Cannot perform 2FA: No email address found for user.", code='authorization')

                # HTML Email Template
                html_message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="UTF-8">
                    <title>{subject}</title>
                    <style>
                        body {{
                            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                            line-height: 1.6;
                            color: #333333;
                            max-width: 600px;
                            margin: 0 auto;
                            padding: 20px;
                            background-color: #f9f9f9;
                        }}
                        .email-container {{
                            background-color: #ffffff;
                            border-radius: 8px;
                            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
                            overflow: hidden;
                        }}
                        .header {{
                            padding: 25px;
                            text-align: center;
                            background-color: #f0f4f8;
                            border-bottom: 1px solid #e0e6ed;
                        }}
                        .logo {{
                            max-height: 50px;
                            margin-bottom: 15px;
                        }}
                        .content {{
                            padding: 25px;
                        }}
                        .otp-code {{
                            font-size: 32px;
                            letter-spacing: 5px;
                            text-align: center;
                            margin: 25px 0;
                            padding: 15px;
                            background-color: #f8fafc;
                            border: 1px dashed #e2e8f0;
                            border-radius: 6px;
                            color: #1e40af;
                            font-weight: bold;
                        }}
                        .footer {{
                            padding: 20px;
                            text-align: center;
                            font-size: 12px;
                            color: #64748b;
                            background-color: #f0f4f8;
                            border-top: 1px solid #e0e6ed;
                        }}
                        .info-box {{
                            background-color: #f8fafc;
                            border-left: 4px solid #4f46e5;
                            padding: 15px;
                            margin: 20px 0;
                            border-radius: 0 4px 4px 0;
                        }}
                        .divider {{
                            height: 1px;
                            background-color: #e2e8f0;
                            margin: 20px 0;
                        }}
                    </style>
                </head>
                <body>
                    <div class="email-container">
                        <div class="header">
                            <img src="{settings.LOGO_URL or 'https://via.placeholder.com/150x50'}" alt="{settings.SITE_NAME or 'App'}" class="logo">
                            <h2 style="margin: 10px 0 0; color: #1e293b;">Login Verification</h2>
                        </div>
                        
                        <div class="content">
                            <p>Hello <strong>{self.user.username}</strong>,</p>
                            
                            <p>We received a login attempt for your {settings.SITE_NAME or 'account'} on {current_time}.</p>
                            
                            <div class="info-box">
                                <p style="margin: 0;">For security reasons, please verify this login attempt using the following One-Time Password:</p>
                            </div>
                            
                            <div class="otp-code">{otp_code}</div>
                            
                            <p>This code will expire in <strong>{expiration_minutes} minutes</strong>.</p>
                            
                            <div class="divider"></div>
                            
                            <p><strong>Security Tips:</strong></p>
                            <ul>
                                <li>Never share this code with anyone</li>
                                <li>This code can only be used once</li>
                                <li>If you didn't request this, please secure your account immediately</li>
                            </ul>
                        </div>
                        
                        <div class="footer">
                            <p>&copy; {timezone.now().year} {settings.SITE_NAME or 'Our App'}. All rights reserved.</p>
                            <p>This email was sent to {recipient} for account security purposes.</p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                # Plain text version
                plain_message = f"""
                Login Verification for {settings.SITE_NAME or 'ITIHub'}
                
                Hello {self.user.username},
                
                We received a login attempt for your account on {current_time}.
                
                Your One-Time Password is:
                {otp_code}
                
                This code will expire in {expiration_minutes} minutes.
                
                Security Tips:
                - Never share this code with anyone
                - This code can only be used once
                - If you didn't request this, please secure your account immediately
                
                © {timezone.now().year} {settings.SITE_NAME or 'Our App'}. All rights reserved.
                """

                # Send email with both HTML and plain text versions
                msg = EmailMultiAlternatives(
                    subject=subject,
                    body=plain_message,
                    from_email=sender,
                    to=[recipient]
                )
                msg.attach_alternative(html_message, "text/html")
                msg.send()

                print(f"2FA enabled for {self.user.username}. OTP sent. Raising OTPAuthenticationFailed.")
                raise self.OTPAuthenticationFailed()

            except Exception as e:
                print(f"Error during OTP generation/sending for {self.user.username}: {e}")
                raise serializers.ValidationError("Could not process two-factor authentication request.", code='authorization')

        else:
            print(f"2FA disabled for {self.user.username}. Generating tokens.")
            refresh = self.get_token(self.user)
            data = {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
            return data

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