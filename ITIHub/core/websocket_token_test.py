from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
import logging
import json
import jwt
import traceback
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings

logger = logging.getLogger(__name__)

@csrf_exempt
def test_token(request):
    """
    Test endpoint to verify token validation logic
    """
    if request.method != 'POST':
        return JsonResponse({"error": "This endpoint only accepts POST requests"}, status=400)
    
    try:
        data = json.loads(request.body)
        token = data.get('token')
        
        if not token:
            return JsonResponse({"error": "No token provided"}, status=400)
            
        results = {
            "token_provided": token[:10] + "..." if len(token) > 10 else token,
            "tests": []
        }
        
        # Test 1: Basic structure check
        parts = token.split('.')
        if len(parts) != 3:
            results["tests"].append({
                "name": "JWT Structure",
                "status": "failed",
                "details": f"Token has {len(parts)} parts instead of 3"
            })
        else:
            results["tests"].append({
                "name": "JWT Structure",
                "status": "success",
                "details": "Token has correct 3-part structure"
            })
            
        # Test 2: JWT manual decode (without verification)
        try:
            decoded = jwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=['HS256', 'RS256']  # Common algorithms
            )
            
            # Check for essential claims
            essential_claims = ['exp', 'iat', 'user_id']
            missing_claims = [claim for claim in essential_claims if claim not in decoded]
            
            if missing_claims:
                results["tests"].append({
                    "name": "Essential Claims",
                    "status": "failed",
                    "details": f"Token is missing required claims: {', '.join(missing_claims)}",
                    "found_claims": list(decoded.keys())
                })
            else:
                results["tests"].append({
                    "name": "Essential Claims",
                    "status": "success",
                    "details": "Token contains all required claims",
                    "claims": {
                        claim: decoded.get(claim) for claim in essential_claims
                    }
                })
                
        except Exception as e:
            results["tests"].append({
                "name": "JWT Decode",
                "status": "failed",
                "details": f"Failed to decode token: {str(e)}"
            })
            
        # Test 3: SimpleJWT Token Verification
        try:
            secret_key = getattr(settings, 'JWT_SECRET_KEY', settings.SECRET_KEY)
            algorithm = api_settings.ALGORITHM
            
            # Full verification using Django REST framework SimpleJWT
            access_token = AccessToken(token)
            user_id = access_token.get('user_id')
            
            results["tests"].append({
                "name": "SimpleJWT Verification",
                "status": "success",
                "details": f"Token is valid, user_id: {user_id}",
            })
            
        except (InvalidToken, TokenError) as e:
            results["tests"].append({
                "name": "SimpleJWT Verification",
                "status": "failed",
                "details": f"Token is invalid: {str(e)}",
            })
        except Exception as e:
            results["tests"].append({
                "name": "SimpleJWT Verification",
                "status": "error",
                "details": f"Error during verification: {str(e)}",
            })
        
        # Test 4: JWT Settings Check
        jwt_settings = {
            "ALGORITHM": api_settings.ALGORITHM,
            "SECRET_KEY_LENGTH": len(secret_key),
            "CUSTOM_JWT_SECRET_KEY_SET": hasattr(settings, 'JWT_SECRET_KEY'),
            "ACCESS_TOKEN_LIFETIME": str(api_settings.ACCESS_TOKEN_LIFETIME),
        }
        
        results["tests"].append({
            "name": "JWT Settings",
            "status": "info",
            "details": "Current JWT settings configuration",
            "settings": jwt_settings
        })
        
        return JsonResponse(results, safe=False)
        
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        logger.error(f"Error testing token: {str(e)}")
        logger.error(traceback.format_exc())
        return JsonResponse({"error": str(e)}, status=500)
