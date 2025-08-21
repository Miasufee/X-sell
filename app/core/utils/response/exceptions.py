from fastapi import HTTPException, status
from typing import Optional, Dict, Any, List, Union


class Exceptions:
    """
    Standardized exception handling for the API.
    Provides methods for different types of exceptions with consistent formatting.
    """

    @staticmethod
    def raise_exception(
            detail: Union[str, Dict[str, Any], List[Dict[str, Any]]],
            status_code: int,
            headers: Optional[Dict[str, str]] = None
    ):
        """
        Base method to raise an HTTPException with consistent formatting.

        Args:
            detail: Error message or structured error data
            status_code: HTTP status code
            headers: Optional HTTP headers (useful for authentication errors)

        Raises:
            HTTPException: FastAPI HTTP exception with the provided details
        """
        raise HTTPException(
            status_code=status_code,
            detail=detail,
            headers=headers
        )

    # ==================== COMMON EXCEPTIONS ====================

    @staticmethod
    def not_found(model_name: Optional[str] = None, detail: Optional[str] = None):
        """404 Not Found exception"""
        message = detail or f"{model_name} not found" if model_name else "Resource not found"
        Exceptions.raise_exception(message, status.HTTP_404_NOT_FOUND)

    @staticmethod
    def no_objects_found(detail: str = "No objects found for deletion"):
        """404 Not Found exception for bulk operations"""
        Exceptions.raise_exception(detail, status.HTTP_404_NOT_FOUND)

    @staticmethod
    def bad_request(detail: str = "Bad request"):
        """400 Bad Request exception"""
        Exceptions.raise_exception(detail, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def invalid_input(errors: Dict[str, List[str]]):
        """400 Bad Request with field-specific validation errors"""
        Exceptions.raise_exception(
            {
                "detail": "Invalid input data",
                "errors": errors
            },
            status.HTTP_400_BAD_REQUEST
        )

    @staticmethod
    def unauthorized(detail: str = "Unauthorized"):
        """401 Unauthorized exception"""
        Exceptions.raise_exception(
            detail,
            status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"}
        )

    @staticmethod
    def forbidden(detail: str = "Forbidden"):
        """403 Forbidden exception"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def method_not_allowed(detail: str = "Method not allowed"):
        """405 Method Not Allowed exception"""
        Exceptions.raise_exception(detail, status.HTTP_405_METHOD_NOT_ALLOWED)

    @staticmethod
    def conflict(detail: str = "Conflict detected"):
        """409 Conflict exception"""
        Exceptions.raise_exception(detail, status.HTTP_409_CONFLICT)

    @staticmethod
    def gone(detail: str = "Resource no longer available"):
        """410 Gone exception"""
        Exceptions.raise_exception(detail, status.HTTP_410_GONE)

    @staticmethod
    def unprocessable_entity(detail: str = "Unprocessable Entity"):
        """422 Unprocessable Entity exception"""
        Exceptions.raise_exception(detail, status.HTTP_422_UNPROCESSABLE_ENTITY)

    @staticmethod
    def too_many_requests(detail: str = "Too many requests"):
        """429 Too Many Requests exception"""
        Exceptions.raise_exception(
            detail,
            status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": "60"}
        )

    @staticmethod
    def internal_server_error(detail: str = "Internal Server Error"):
        """500 Internal Server Error exception"""
        Exceptions.raise_exception(detail, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def service_unavailable(detail: str = "Service temporarily unavailable"):
        """503 Service Unavailable exception"""
        Exceptions.raise_exception(
            detail,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Retry-After": "120"}
        )

    # ==================== AUTHENTICATION & AUTHORIZATION EXCEPTIONS ====================

    @staticmethod
    def email_exist(detail: str = "Email already exists"):
        """409 Conflict exception for email registration"""
        Exceptions.raise_exception(detail, status.HTTP_409_CONFLICT)

    @staticmethod
    def username_exist(detail: str = "Username already exists"):
        """409 Conflict exception for username registration"""
        Exceptions.raise_exception(detail, status.HTTP_409_CONFLICT)

    @staticmethod
    def email_not_registered(detail: str = "Email is not registered"):
        """404 Not Found exception for email login"""
        Exceptions.raise_exception(detail, status.HTTP_404_NOT_FOUND)

    @staticmethod
    def invalid_credentials(detail: str = "Invalid email or password"):
        """401 Unauthorized exception for login"""
        Exceptions.raise_exception(detail, status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def account_locked(detail: str = "Account is locked due to too many failed login attempts"):
        """403 Forbidden exception for locked accounts"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def account_disabled(detail: str = "Account has been disabled"):
        """403 Forbidden exception for disabled accounts"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def not_verified(detail: str = "User is not verified"):
        """403 Forbidden exception for unverified users"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def invalid_verification_code(detail: str = "Invalid verification code"):
        """403 Forbidden exception for invalid verification codes"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def verification_code_expired(detail: str = "Verification code has expired"):
        """403 Forbidden exception for expired verification codes"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def already_verified(detail: str = "Account is already verified"):
        """409 Conflict exception for already verified accounts"""
        Exceptions.raise_exception(detail, status.HTTP_409_CONFLICT)

    @staticmethod
    def invalid_token(detail: str = "Invalid or expired token"):
        """401 Unauthorized exception for invalid tokens"""
        Exceptions.raise_exception(
            detail,
            status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"}
        )

    @staticmethod
    def token_expired(detail: str = "Token has expired"):
        """401 Unauthorized exception for expired tokens"""
        Exceptions.raise_exception(
            detail,
            status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Bearer"}
        )

    @staticmethod
    def refresh_token_invalid(detail: str = "Invalid refresh token"):
        """401 Unauthorized exception for invalid refresh tokens"""
        Exceptions.raise_exception(detail, status.HTTP_401_UNAUTHORIZED)

    @staticmethod
    def insufficient_permissions(detail: str = "Insufficient permissions"):
        """403 Forbidden exception for permission issues"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def role_required(role: str):
        """403 Forbidden exception for role requirements"""
        Exceptions.raise_exception(f"{role} role required", status.HTTP_403_FORBIDDEN)

    # ==================== USER MANAGEMENT EXCEPTIONS ====================

    @staticmethod
    def user_not_found(detail: str = "User not found"):
        """404 Not Found exception for users"""
        Exceptions.raise_exception(detail, status.HTTP_404_NOT_FOUND)

    @staticmethod
    def password_too_weak(detail: str = "Password does not meet security requirements"):
        """400 Bad Request exception for weak passwords"""
        Exceptions.raise_exception(detail, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def password_mismatch(detail: str = "Passwords do not match"):
        """400 Bad Request exception for password confirmation"""
        Exceptions.raise_exception(detail, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def current_password_incorrect(detail: str = "Current password is incorrect"):
        """400 Bad Request exception for password change"""
        Exceptions.raise_exception(detail, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def password_reset_expired(detail: str = "Password reset link has expired"):
        """410 Gone exception for expired password reset links"""
        Exceptions.raise_exception(detail, status.HTTP_410_GONE)

    @staticmethod
    def profile_not_found(detail: str = "User profile not found"):
        """404 Not Found exception for user_management profiles"""
        Exceptions.raise_exception(detail, status.HTTP_404_NOT_FOUND)

    # ==================== CONTENT & RESOURCE EXCEPTIONS ====================

    @staticmethod
    def content_not_found(content_type: str = "Content"):
        """404 Not Found exception for content"""
        Exceptions.raise_exception(f"{content_type} not found", status.HTTP_404_NOT_FOUND)

    @staticmethod
    def file_too_large(max_size_mb: int):
        """413 Request Entity Too Large exception for file uploads"""
        Exceptions.raise_exception(
            f"File exceeds maximum size of {max_size_mb}MB",
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
        )

    @staticmethod
    def invalid_file_type(allowed_types: List[str]):
        """415 Unsupported Media Type exception for file uploads"""
        Exceptions.raise_exception(
            f"File type not supported. Allowed types: {', '.join(allowed_types)}",
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE
        )

    @staticmethod
    def upload_failed(detail: str = "File upload failed"):
        """500 Internal Server Error exception for file uploads"""
        Exceptions.raise_exception(detail, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def resource_in_use(resource_type: str, resource_id: str):
        """409 Conflict exception for resources in use"""
        Exceptions.raise_exception(
            f"{resource_type} with ID {resource_id} is currently in use",
            status.HTTP_409_CONFLICT
        )

    # ==================== PAYMENT & SUBSCRIPTION EXCEPTIONS ====================

    @staticmethod
    def payment_required(detail: str = "Payment required to access this resource"):
        """402 Payment Required exception"""
        Exceptions.raise_exception(detail, status.HTTP_402_PAYMENT_REQUIRED)

    @staticmethod
    def payment_failed(detail: str = "Payment processing failed"):
        """400 Bad Request exception for payment failures"""
        Exceptions.raise_exception(detail, status.HTTP_400_BAD_REQUEST)

    @staticmethod
    def subscription_expired(detail: str = "Subscription has expired"):
        """403 Forbidden exception for expired subscriptions"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def subscription_limit_reached(detail: str = "Subscription limit reached"):
        """403 Forbidden exception for subscription limits"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def invalid_coupon(detail: str = "Invalid or expired coupon code"):
        """400 Bad Request exception for invalid coupons"""
        Exceptions.raise_exception(detail, status.HTTP_400_BAD_REQUEST)

    # ==================== RATE LIMITING & SECURITY EXCEPTIONS ====================

    @staticmethod
    def rate_limit_exceeded(detail: str = "Rate limit exceeded"):
        """429 Too Many Requests exception for rate limiting"""
        Exceptions.raise_exception(
            detail,
            status.HTTP_429_TOO_MANY_REQUESTS,
            headers={"Retry-After": "60"}
        )

    @staticmethod
    def ip_blocked(detail: str = "Your IP address has been temporarily blocked"):
        """403 Forbidden exception for blocked IPs"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    @staticmethod
    def csrf_token_invalid(detail: str = "Invalid CSRF token"):
        """403 Forbidden exception for CSRF protection"""
        Exceptions.raise_exception(detail, status.HTTP_403_FORBIDDEN)

    # ==================== EXTERNAL SERVICE EXCEPTIONS ====================

    @staticmethod
    def external_service_error(service_name: str, detail: Optional[str] = None):
        """502 Bad Gateway exception for external service errors"""
        message = detail or f"Error communicating with external service: {service_name}"
        Exceptions.raise_exception(message, status.HTTP_502_BAD_GATEWAY)

    @staticmethod
    def database_error(detail: str = "Database operation failed"):
        """500 Internal Server Error exception for database errors"""
        Exceptions.raise_exception(detail, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @staticmethod
    def cache_error(detail: str = "Cache operation failed"):
        """500 Internal Server Error exception for cache errors"""
        Exceptions.raise_exception(detail, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== VALIDATION EXCEPTIONS ====================

    @staticmethod
    def validation_error(errors: Dict[str, List[str]]):
        """422 Unprocessable Entity exception with field-specific validation errors"""
        Exceptions.raise_exception(
            {
                "detail": "Validation error",
                "errors": errors
            },
            status.HTTP_422_UNPROCESSABLE_ENTITY
        )

    @staticmethod
    def invalid_query_params(errors: Dict[str, str]):
        """400 Bad Request exception for invalid query parameters"""
        Exceptions.raise_exception(
            {
                "detail": "Invalid query parameters",
                "errors": errors
            },
            status.HTTP_400_BAD_REQUEST
        )

    @staticmethod
    def invalid_date_range(detail: str = "Invalid date range"):
        """400 Bad Request exception for invalid date ranges"""
        Exceptions.raise_exception(detail, status.HTTP_400_BAD_REQUEST)

    # ==================== CUSTOM EXCEPTIONS ====================

    @staticmethod
    def custom_exception(detail: str, status_code: int, headers: Optional[Dict[str, str]] = None):
        """Custom exception with specified status code and optional headers"""
        Exceptions.raise_exception(detail, status_code, headers)

    @staticmethod
    def feature_not_implemented(detail: str = "This feature is not yet implemented"):
        """501 Not Implemented exception"""
        Exceptions.raise_exception(detail, status.HTTP_501_NOT_IMPLEMENTED)

    @staticmethod
    def maintenance_mode(detail: str = "Service is currently in maintenance mode"):
        """503 Service Unavailable exception for maintenance"""
        Exceptions.raise_exception(
            detail,
            status.HTTP_503_SERVICE_UNAVAILABLE,
            headers={"Retry-After": "3600"}
        )

    @staticmethod
    def credentials_exception():
        Exceptions.raise_exception(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    @classmethod
    def permission_denied(cls, detail: str = "Permission denied"):
        """403 Forbidden exception for insufficient permissions"""
        cls.forbidden(detail)
